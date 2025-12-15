"""
Kalshi API Client
Streamlined client for Kalshi trading API with authentication and order execution.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

import requests
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Kalshi API environment options."""
    DEMO = "demo"
    PROD = "prod"


class KalshiClient:
    """
    Streamlined Kalshi client for trading operations.
    Handles authentication, market data fetching, and order execution.
    """

    def __init__(
        self,
        key_id: Optional[str] = None,
        private_key: Optional[rsa.RSAPrivateKey] = None,
        environment: Environment = Environment.DEMO
    ):
        """
        Initialize Kalshi client.
        
        Args:
            key_id: Kalshi API key ID
            private_key: RSA private key for authentication
            environment: DEMO or PROD environment
        """
        self.key_id = key_id or os.getenv('KALSHI_API_KEY_ID')
        self.environment = environment
        self.last_api_call = datetime.now()
        
        # Load private key if not provided
        if private_key is None:
            # Option 1: Try inline private key from environment variable
            inline_key = os.getenv('KALSHI_PRIVATE_KEY')
            if inline_key:
                try:
                    # Handle escaped newlines in the key
                    key_content = inline_key.replace('\\n', '\n').encode('utf-8')
                    self.private_key = serialization.load_pem_private_key(
                        key_content,
                        password=None
                    )
                except Exception as e:
                    logger.error(f"Failed to load inline private key: {e}")
                    self.private_key = None
            else:
                # Option 2: Try loading from file path
                key_file_path = os.getenv('KALSHI_PRIVATE_KEY_PATH')
                if key_file_path and os.path.exists(key_file_path):
                    with open(key_file_path, 'rb') as key_file:
                        self.private_key = serialization.load_pem_private_key(
                            key_file.read(),
                            password=None
                        )
                else:
                    self.private_key = None
        else:
            self.private_key = private_key
        
        # Set API endpoints based on environment
        if self.environment == Environment.DEMO:
            self.http_base_url = "https://demo-api.kalshi.co"
            self.ws_base_url = "wss://demo-api.kalshi.co"
        else:
            self.http_base_url = "https://api.elections.kalshi.com"
            self.ws_base_url = "wss://api.elections.kalshi.com"
        
        # API path prefixes
        self.exchange_url = "/trade-api/v2/exchange"
        self.markets_url = "/trade-api/v2/markets"
        self.portfolio_url = "/trade-api/v2/portfolio"
        self.orders_url = "/trade-api/v2/portfolio/orders"
        
        # Determine mode
        if self.key_id and self.private_key:
            self.mode = "trading"
            logger.info("Initialized Kalshi client in trading mode")
        else:
            self.mode = "read-only"
            logger.warning("Initialized Kalshi client in read-only mode (no credentials)")

    def _sign_pss_text(self, text: str) -> str:
        """Sign text using RSA-PSS and return base64 encoded signature."""
        if not self.private_key:
            raise ValueError("Private key required for authentication")
        
        message = text.encode('utf-8')
        try:
            signature = self.private_key.sign(
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH
                ),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode('utf-8')
        except InvalidSignature as e:
            raise ValueError("RSA sign PSS failed") from e

    def _request_headers(self, method: str, path: str) -> Dict[str, Any]:
        """Generate authentication headers for API requests."""
        if not self.key_id or not self.private_key:
            return {"Content-Type": "application/json"}
        
        current_time_milliseconds = int(time.time() * 1000)
        timestamp_str = str(current_time_milliseconds)
        
        # Remove query params from path for signature
        path_parts = path.split('?')
        msg_string = timestamp_str + method + path_parts[0]
        signature = self._sign_pss_text(msg_string)
        
        return {
            "Content-Type": "application/json",
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp_str,
        }

    def _rate_limit(self) -> None:
        """Rate limiter to prevent exceeding API limits."""
        THRESHOLD_IN_MILLISECONDS = 100
        now = datetime.now()
        threshold_in_microseconds = 1000 * THRESHOLD_IN_MILLISECONDS
        threshold_in_seconds = THRESHOLD_IN_MILLISECONDS / 1000
        if now - self.last_api_call < timedelta(microseconds=threshold_in_microseconds):
            time.sleep(threshold_in_seconds)
        self.last_api_call = datetime.now()

    def _raise_if_bad_response(self, response: requests.Response) -> None:
        """Raise HTTPError if response indicates an error."""
        if response.status_code not in range(200, 299):
            logger.error(f"API error: {response.status_code} - {response.text}")
            response.raise_for_status()

    def get(self, path: str, params: Dict[str, Any] = None) -> Any:
        """Perform authenticated GET request."""
        self._rate_limit()
        params = params or {}
        response = requests.get(
            self.http_base_url + path,
            headers=self._request_headers("GET", path),
            params=params
        )
        self._raise_if_bad_response(response)
        return response.json()

    def post(self, path: str, body: Dict[str, Any]) -> Any:
        """Perform authenticated POST request."""
        self._rate_limit()
        response = requests.post(
            self.http_base_url + path,
            json=body,
            headers=self._request_headers("POST", path)
        )
        self._raise_if_bad_response(response)
        return response.json()

    def delete(self, path: str, params: Dict[str, Any] = None) -> Any:
        """Perform authenticated DELETE request."""
        self._rate_limit()
        params = params or {}
        response = requests.delete(
            self.http_base_url + path,
            headers=self._request_headers("DELETE", path),
            params=params
        )
        self._raise_if_bad_response(response)
        return response.json()

    # Market Data Methods
    
    def get_markets(
        self,
        limit: Optional[int] = 100,
        cursor: Optional[str] = None,
        status: Optional[str] = None,
        series_ticker: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get markets with optional filters."""
        params = {}
        if limit:
            params['limit'] = limit
        if cursor:
            params['cursor'] = cursor
        if status:
            params['status'] = status
        if series_ticker:
            params['series_ticker'] = series_ticker
        
        return self.get(self.markets_url, params)

    def get_market(self, ticker: str) -> Dict[str, Any]:
        """Get specific market by ticker."""
        return self.get(f"{self.markets_url}/{ticker}")

    def get_orderbook(self, ticker: str, depth: Optional[int] = None) -> Dict[str, Any]:
        """Get orderbook for a specific market."""
        params = {}
        if depth:
            params['depth'] = depth
        return self.get(f"{self.markets_url}/{ticker}/orderbook", params)

    def get_trades(
        self,
        ticker: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        max_ts: Optional[int] = None,
        min_ts: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get recent trades."""
        params = {}
        if ticker:
            params['ticker'] = ticker
        if limit:
            params['limit'] = limit
        if cursor:
            params['cursor'] = cursor
        if max_ts:
            params['max_ts'] = max_ts
        if min_ts:
            params['min_ts'] = min_ts
        
        return self.get(f"{self.markets_url}/trades", params)

    # Portfolio Methods
    
    def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        if self.mode != "trading":
            logger.warning("Cannot get balance in read-only mode")
            return {}
        return self.get(f"{self.portfolio_url}/balance")

    def get_positions(self) -> Dict[str, Any]:
        """Get current positions."""
        if self.mode != "trading":
            logger.warning("Cannot get positions in read-only mode")
            return {}
        return self.get(f"{self.portfolio_url}/positions")

    # Order Methods
    
    def create_order(
        self,
        ticker: str,
        action: str,  # "buy" or "sell"
        side: str,  # "yes" or "no"
        count: int,  # Number of contracts
        order_type: str = "market",  # "market" or "limit"
        yes_price: Optional[int] = None,  # Price in cents (for limit orders)
        no_price: Optional[int] = None,
        expiration_ts: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create an order on Kalshi.
        
        Args:
            ticker: Market ticker
            action: "buy" or "sell"
            side: "yes" or "no"
            count: Number of contracts
            order_type: "market" or "limit"
            yes_price: Price in cents for yes side (limit orders)
            no_price: Price in cents for no side (limit orders)
            expiration_ts: Unix timestamp for order expiration
            
        Returns:
            Order response dict or None if failed
        """
        if self.mode != "trading":
            logger.warning("Cannot create orders in read-only mode")
            return None

        try:
            order_data = {
                "ticker": ticker,
                "action": action,
                "side": side,
                "count": count,
                "type": order_type
            }
            
            if order_type == "limit":
                if yes_price is not None:
                    order_data["yes_price"] = yes_price
                if no_price is not None:
                    order_data["no_price"] = no_price
            
            if expiration_ts:
                order_data["expiration_ts"] = expiration_ts
            
            result = self.post(self.orders_url, order_data)
            logger.info(f"Created {action} {side} order for {ticker}: {count} contracts")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            return None

    def execute_market_order(
        self,
        ticker: str,
        side: str,  # "yes" or "no"
        count: int,
        action: str = "buy"
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a market order for immediate execution.
        
        Args:
            ticker: Market ticker
            side: "yes" or "no"
            count: Number of contracts
            action: "buy" or "sell"
            
        Returns:
            Order response or None if failed
        """
        return self.create_order(
            ticker=ticker,
            action=action,
            side=side,
            count=count,
            order_type="market"
        )

    def get_orders(
        self,
        ticker: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get orders with optional filters."""
        if self.mode != "trading":
            logger.warning("Cannot get orders in read-only mode")
            return {}
        
        params = {}
        if ticker:
            params['ticker'] = ticker
        if status:
            params['status'] = status
        
        return self.get(self.orders_url, params)

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a specific order."""
        if self.mode != "trading":
            logger.warning("Cannot cancel orders in read-only mode")
            return {}
        
        return self.delete(f"{self.orders_url}/{order_id}")

    # Exchange Methods
    
    def get_exchange_status(self) -> Dict[str, Any]:
        """Get exchange status."""
        return self.get(f"{self.exchange_url}/status")

    def get_exchange_announcements(self) -> Dict[str, Any]:
        """Get exchange-wide announcements."""
        return self.get(f"{self.exchange_url}/announcements")


# Global client instance for reuse
_kalshi_client = None


def get_kalshi_client() -> KalshiClient:
    """Get or create Kalshi client instance."""
    global _kalshi_client
    if _kalshi_client is None:
        # Determine environment from env var
        env_str = os.getenv('KALSHI_ENVIRONMENT', 'DEMO').upper()
        environment = Environment.DEMO if env_str == 'DEMO' else Environment.PROD
        _kalshi_client = KalshiClient(environment=environment)
    return _kalshi_client
