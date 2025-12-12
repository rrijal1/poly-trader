"""
BTC Conditional Probability Strategy
Exploits inefficiencies in conditional probabilities between strike prices.
Logic: Compare Market Implied Conditional Probability vs Theoretical Conditional Probability.
P(BTC > K2 | BTC > K1) = P(BTC > K2) / P(BTC > K1)
"""

import logging
import requests
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import re

from common import TradeSignal, get_clob_client

logger = logging.getLogger(__name__)

@dataclass
class BTCMarket:
    market_id: str
    question: str
    strike_price: float
    expiry_date: datetime
    yes_price: float
    no_price: float
    token_ids: List[str]
    volume: float

class DeribitService:
    """Service to fetch option volatility data from Deribit."""
    
    BASE_URL = "https://www.deribit.com/api/v2/public"
    
    @staticmethod
    def get_btc_volatility_index() -> Optional[float]:
        """Get current BTC DVOL (Volatility Index)."""
        try:
            # DVOL is 30-day forward looking volatility
            # Note: The endpoint might change, using get_volatility_index_data
            url = f"{DeribitService.BASE_URL}/get_volatility_index_data?currency=BTC&resolution=3600"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and 'data' in data['result'] and data['result']['data']:
                    # Last data point, value is at index 1
                    dvol = data['result']['data'][-1][1]
                    return float(dvol) / 100.0 # Convert 65.5 -> 0.655
            return None
        except Exception as e:
            logger.error(f"Error fetching Deribit DVOL: {e}")
            return None

    @staticmethod
    def get_option_iv(expiry_date: datetime, strike: float) -> Optional[float]:
        """
        Get IV for a specific option from Deribit.
        Finds the closest matching option instrument.
        """
        try:
            url = f"{DeribitService.BASE_URL}/get_book_summary_by_currency?currency=BTC&kind=option"
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                return None
                
            data = response.json()
            options = data.get('result', [])
            
            # Deribit format: BTC-29DEC23-100000-C
            # Polymarket expiry might not match Deribit exactly.
            # We should look for the closest expiry in Deribit.
            
            target_timestamp = expiry_date.timestamp()
            
            best_match = None
            min_score = float('inf') # Score = weighted diff of expiry and strike
            
            for opt in options:
                # Parse instrument name
                parts = opt['instrument_name'].split('-')
                if len(parts) < 4: continue
                
                opt_expiry_str = parts[1]
                opt_strike = float(parts[2])
                
                try:
                    # Parse Deribit expiry "29DEC23"
                    opt_expiry_dt = datetime.strptime(opt_expiry_str, "%d%b%y").replace(tzinfo=timezone.utc)
                    # Adjust year if needed (Deribit uses 2 digits)
                    # Actually strptime %y handles it (69-99 -> 1900s, 00-68 -> 2000s)
                    
                    # Calculate time difference in days
                    days_diff = abs((opt_expiry_dt - expiry_date).days)
                    
                    # If expiry is too far off (> 2 days), skip
                    if days_diff > 2:
                        continue
                        
                    # Calculate strike difference
                    strike_diff = abs(opt_strike - strike)
                    
                    # Score: prioritize expiry match, then strike match
                    # We want exact expiry if possible.
                    score = (days_diff * 10000) + strike_diff
                    
                    if score < min_score:
                        min_score = score
                        best_match = opt
                        
                except ValueError:
                    continue
            
            if best_match and 'mark_iv' in best_match:
                iv = float(best_match['mark_iv']) / 100.0
                logger.info(f"Found matching Deribit option: {best_match['instrument_name']} IV: {iv:.2%}")
                return iv
                
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Deribit Option IV: {e}")
            return None

class BTCPricePredictionStrategy:
    """
    Production-ready strategy for BTC markets using Conditional Probability Analysis.
    
    Identifies mispricing where the market's implied probability of reaching a higher strike
    (given it has reached a lower strike) diverges significantly from theoretical models.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.client = get_clob_client()
        self.min_edge = config.get('min_edge', 0.10)  # 10% probability edge required
        self.risk_free_rate = 0.045  # 4.5% risk free rate
        self.fixed_volatility = config.get('fixed_volatility', 0.65) # Fallback vol if IV calc fails
        self.use_deribit_vol = config.get('use_deribit_vol', True)
        
    def get_current_btc_price(self) -> Optional[float]:
        """Fetch real-time BTC price from CoinGecko."""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                price = response.json()['bitcoin']['usd']
                logger.info(f"Current BTC Price: ${price:,.2f}")
                return price
            else:
                logger.error(f"Failed to fetch BTC price: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching BTC price: {e}")
            return None

    def parse_market(self, market_data: Dict) -> Optional[BTCMarket]:
        """Parse market data into structured BTCMarket object."""
        question = market_data.get('question', '')
        
        # Filter for BTC price markets
        if 'Bitcoin' not in question and 'BTC' not in question:
            return None
            
        # Regex to extract strike price
        # Matches: "Will Bitcoin be above $100,000..."
        price_match = re.search(r'\$?([\d,]+\.?\d*)', question)
        if not price_match:
            return None
            
        try:
            strike_price = float(price_match.group(1).replace(',', ''))
        except ValueError:
            return None

        # Parse expiry date
        expiry_str = market_data.get('end_date_iso', '')
        if not expiry_str:
            return None
            
        try:
            # Handle ISO format (e.g., "2025-12-31T23:59:59Z")
            expiry_date = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
        except ValueError:
            return None
        
        return BTCMarket(
            market_id=market_data['market_id'],
            question=question,
            strike_price=strike_price,
            expiry_date=expiry_date,
            yes_price=float(market_data.get('yes_price', 0) or 0),
            no_price=float(market_data.get('no_price', 0) or 0),
            token_ids=market_data.get('token_ids', []),
            volume=float(market_data.get('volume', 0) or 0)
        )

    def _norm_cdf(self, x):
        """Cumulative distribution function for the standard normal distribution."""
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

    def calculate_theoretical_prob(self, S: float, K: float, T: float, sigma: float) -> float:
        """
        Calculate theoretical probability P(S_T > K) using Black-Scholes logic.
        In risk-neutral world, this is N(d2).
        """
        if T <= 0:
            return 1.0 if S > K else 0.0
            
        d2 = (math.log(S / K) + (self.risk_free_rate - 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        return self._norm_cdf(d2)

    def calculate_implied_vol(self, price: float, S: float, K: float, T: float) -> float:
        """
        Estimate implied volatility from market price.
        Simple binary search or approximation.
        """
        if price <= 0.01 or price >= 0.99:
            return self.fixed_volatility # Too extreme to calculate reliable IV
            
        low, high = 0.1, 3.0 # Volatility range 10% to 300%
        for _ in range(10):
            mid = (low + high) / 2
            prob = self.calculate_theoretical_prob(S, K, T, mid)
            if prob < price:
                high = mid # Need lower vol (usually? depends on moneyness)
                # Wait, if S < K (OTM), higher vol -> higher prob.
                # If S > K (ITM), higher vol -> lower prob (time value erosion).
                # Let's handle direction correctly.
                if S < K:
                    low = mid # Need higher vol to reach OTM strike
                else:
                    high = mid # Need lower vol to maintain ITM probability
            else:
                if S < K:
                    high = mid
                else:
                    low = mid
        return (low + high) / 2

    def analyze_conditional_probabilities(self, markets: List[BTCMarket], current_btc_price: float) -> List[TradeSignal]:
        """
        Analyze conditional probabilities between strikes.
        """
        signals = []
        now = datetime.now(timezone.utc)
        
        # Group by expiry
        markets_by_expiry = {}
        for m in markets:
            if m.expiry_date <= now:
                continue
            if m.expiry_date not in markets_by_expiry:
                markets_by_expiry[m.expiry_date] = []
            markets_by_expiry[m.expiry_date].append(m)
            
        for expiry, expiry_markets in markets_by_expiry.items():
            # Sort by strike price
            sorted_markets = sorted(expiry_markets, key=lambda x: x.strike_price)
            
            # Calculate Time to Expiry (in years)
            T = (expiry - now).total_seconds() / (365 * 24 * 3600)
            if T < 0.001: continue # Too close to expiry
            
            # 1. Determine Baseline Volatility
            # Priority 1: Deribit ATM Option IV (Specific Expiry)
            # Priority 2: Deribit DVOL (Market Truth)
            # Priority 3: Implied Vol from Polymarket ATM (if liquid)
            # Priority 4: Fixed Fallback
            
            baseline_vol = None
            
            if self.use_deribit_vol:
                # Try to get specific option IV first
                atm_iv = DeribitService.get_option_iv(expiry, current_btc_price)
                if atm_iv:
                    baseline_vol = atm_iv
                    logger.info(f"Using Deribit ATM IV: {atm_iv:.2%}")
                else:
                    # Fallback to DVOL
                    dvol = DeribitService.get_btc_volatility_index()
                    if dvol:
                        baseline_vol = dvol
                        logger.info(f"Using Deribit DVOL: {dvol:.2%}")
            
            if baseline_vol is None:
                # Fallback to Polymarket ATM IV
                anchor_market = min(sorted_markets, key=lambda x: abs(x.strike_price - current_btc_price))
                if 0.05 < anchor_market.yes_price < 0.95:
                    baseline_vol = self.calculate_implied_vol(anchor_market.yes_price, current_btc_price, anchor_market.strike_price, T)
                    logger.info(f"Using Polymarket ATM IV: {baseline_vol:.2%}")
                else:
                    baseline_vol = self.fixed_volatility
                    logger.info(f"Using Fixed Fallback Vol: {baseline_vol:.2%}")
                
            logger.info(f"Expiry: {expiry}, T={T:.4f}, Baseline Vol: {baseline_vol:.2%}")

            # 2. Analyze Pairs
            for i in range(len(sorted_markets) - 1):
                m1 = sorted_markets[i]      # Lower Strike (e.g. 95k)
                m2 = sorted_markets[i+1]    # Higher Strike (e.g. 100k)
                
                # Skip illiquid markets
                if m1.yes_price == 0 or m2.yes_price == 0: continue
                
                # Market Implied Conditional Probability: P(>K2 | >K1)
                # P(A|B) = P(A and B) / P(B). Since >K2 implies >K1, P(>K2 and >K1) = P(>K2).
                # So P(>K2 | >K1) = P(>K2) / P(>K1)
                # = Price(M2) / Price(M1)
                
                if m1.yes_price < 0.01: continue # Avoid division by zero
                
                # Ensure monotonicity: Price(M2) should be <= Price(M1)
                # If Price(M2) > Price(M1), it's a pure arbitrage (handled by other logic),
                # but for conditional prob calc, we cap it at 1.0
                if m2.yes_price > m1.yes_price:
                    market_cond_prob = 1.0
                else:
                    market_cond_prob = m2.yes_price / m1.yes_price
                
                # Theoretical Conditional Probability
                prob_m1 = self.calculate_theoretical_prob(current_btc_price, m1.strike_price, T, baseline_vol)
                prob_m2 = self.calculate_theoretical_prob(current_btc_price, m2.strike_price, T, baseline_vol)
                
                if prob_m1 < 0.001: continue
                
                model_cond_prob = prob_m2 / prob_m1
                
                # Calculate Edge
                # If Market Cond Prob << Model Cond Prob: Market underestimates chance of reaching K2 given K1.
                # Opportunity: Buy M2 (Cheap).
                
                edge = model_cond_prob - market_cond_prob
                
                logger.info(f"  Pair {m1.strike_price}k -> {m2.strike_price}k: "
                           f"Mkt Cond: {market_cond_prob:.2%} | Model Cond: {model_cond_prob:.2%} | Edge: {edge:.2%}")
                
                if edge > self.min_edge:
                    # Market underestimates the conditional step. Buy the higher strike.
                    # Example: Mkt says 25% chance to go 95->100. Model says 70%.
                    # Buy 100k YES.
                    signals.append(TradeSignal(
                        market_id=m2.market_id,
                        action='buy_yes',
                        price=m2.yes_price,
                        size=self.config.get('max_size', 50),
                        reason=f"Cond Prob Edge: Mkt {market_cond_prob:.1%} < Model {model_cond_prob:.1%} (Vol {baseline_vol:.0%})",
                        confidence=min(1.0, edge * 5), # Scale confidence
                        token_id=m2.token_ids[0]
                    ))
                
                elif edge < -self.min_edge:
                    # Market overestimates the conditional step. Sell the higher strike (Buy NO).
                    # Mkt says 95% chance to go 95->100. Model says 70%.
                    # Buy 100k NO.
                    signals.append(TradeSignal(
                        market_id=m2.market_id,
                        action='buy_no',
                        price=m2.no_price,
                        size=self.config.get('max_size', 50),
                        reason=f"Cond Prob Edge: Mkt {market_cond_prob:.1%} > Model {model_cond_prob:.1%} (Vol {baseline_vol:.0%})",
                        confidence=min(1.0, abs(edge) * 5),
                        token_id=m2.token_ids[1]
                    ))
                    
        return signals

    def analyze_markets(self, markets_df: pd.DataFrame) -> List[TradeSignal]:
        """Analyze multiple markets for conditional probability opportunities."""
        btc_markets = []
        
        # 1. Parse all markets
        for _, row in markets_df.iterrows():
            market_obj = self.parse_market(row.to_dict())
            if market_obj:
                btc_markets.append(market_obj)
                
        if not btc_markets:
            return []
            
        # 2. Get Real Price
        current_price = self.get_current_btc_price()
        if not current_price:
            return []
        
        # 3. Analyze Conditional Probabilities
        signals = self.analyze_conditional_probabilities(btc_markets, current_price)
        
        return signals
