# Polymarket Agent Wallet Setup Guide

This guide shows how to set up **trading-only agent wallets** for Polymarket. Agent wallets can place trades but cannot withdraw funds, providing enhanced security for automated trading.

## 🛡️ Security Assessment

Based on official Polymarket CLOB documentation:

### How Agent Wallets Work
1. **Agent signs orders** using `signature_type=1` (delegated signing)
2. **Funder provides funds** - orders are attributed to funder address
3. **Exchange executes trades** using funder's collateral
4. **Withdrawals require funder** - agent cannot access funds directly

### Why Agent Cannot Withdraw
- **No direct fund access**: Funds remain attributed to funder address
- **Separate withdrawal process**: Requires funder wallet signature
- **Contract-level security**: Exchange contracts enforce funder control
- **Non-custodial**: Operator never controls user funds

### Official Documentation Confirmation
From Polymarket CLOB docs:
> "The funder address is the actual address that holds your funds on Polymarket. When using proxy wallets, the signing key differs from the address holding the funds."

> "Private key authentication is required for: Placing an order, Creating or revoking API keys"

> "The operator never has control over users' funds. Trading is non-custodial."

## 🔐 Security Model

### Agent Wallet (Trading Only)

- ✅ **Can place orders** (market orders, limit orders)
- ✅ **Can cancel orders**
- ✅ **Can check balances and positions**
- ❌ **Cannot withdraw funds**
- ❌ **Cannot transfer USDC**
- ❌ **Cannot change allowances**

### Funder Wallet (Funds Control)

- ✅ **Holds all USDC funds**
- ✅ **Controls withdrawals**
- ✅ **Manages token allowances**
- ✅ **Complete fund security**

## 🛠️ Setup Process

### Step 1: Create Wallets

Create two separate wallets:

```bash
# Install dependencies
pip install web3 eth-account

# Create agent wallet (for trading)
python3 -c "
from eth_account import Account
agent = Account.create()
print('Agent Private Key:', agent.key.hex())
print('Agent Address:', agent.address)
"

# Create funder wallet (for funds - keep this ultra-secure)
python3 -c "
from eth_account import Account
funder = Account.create()
print('Funder Private Key:', funder.key.hex())
print('Funder Address:', funder.address)
"
```

### Step 2: Fund the Funder Wallet

Send USDC to your **funder wallet address** on Polygon network:

- **Network**: Polygon (not Ethereum mainnet)
- **Token**: USDC (0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174)
- **Amount**: Your trading budget + gas fees

### Step 3: Set Token Allowances

**Important**: Allowances must be set from the **funder wallet** (not agent):

```python
# Run this script with your FUNDER wallet private key
from web3 import Web3
from eth_account import Account

# Connect to Polygon
w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com/'))

# Your funder wallet (the one with funds)
FUNDER_PRIVATE_KEY = '0x...'  # Funder wallet private key
FUNDER_ADDRESS = '0x...'      # Funder wallet address

# Contract addresses (Polygon mainnet)
USDC_CONTRACT = '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174'
CONDITIONAL_TOKENS = '0x4D97DCd97eC945f40cF65F87097ACe5EA0476045'
EXCHANGE_CONTRACTS = [
    '0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E',  # Main exchange
    '0xC5d563A36AE78145C45a50134d48A1215220f80a',  # Neg risk markets
    '0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296'   # Neg risk adapter
]

# Set unlimited allowances for USDC
usdc_abi = [...]  # ERC20 ABI
usdc_contract = w3.eth.contract(address=USDC_CONTRACT, abi=usdc_abi)

for exchange in EXCHANGE_CONTRACTS:
    tx = usdc_contract.functions.approve(exchange, 2**256-1).build_transaction({
        'from': FUNDER_ADDRESS,
        'nonce': w3.eth.get_transaction_count(FUNDER_ADDRESS),
        'gas': 100000,
        'gasPrice': w3.eth.gas_price
    })
    signed = w3.eth.account.sign_transaction(tx, FUNDER_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"USDC approval sent: {tx_hash.hex()}")

# Set unlimited allowances for Conditional Tokens
ct_abi = [...]  # ERC1155 ABI
ct_contract = w3.eth.contract(address=CONDITIONAL_TOKENS, abi=ct_abi)

for exchange in EXCHANGE_CONTRACTS:
    tx = ct_contract.functions.setApprovalForAll(exchange, True).build_transaction({
        'from': FUNDER_ADDRESS,
        'nonce': w3.eth.get_transaction_count(FUNDER_ADDRESS),
        'gas': 100000,
        'gasPrice': w3.eth.gas_price
    })
    signed = w3.eth.account.sign_transaction(tx, FUNDER_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"Conditional tokens approval sent: {tx_hash.hex()}")
```

### Step 4: Configure Environment Variables

For each strategy, create a `.env` file:

```bash
# Copy the example
cp .env.example .env

# Edit with your wallet information
# Agent wallet private key (can trade, cannot withdraw)
POLYGON_WALLET_PRIVATE_KEY=0x_agent_wallet_private_key_here

# Funder wallet address (holds the funds)
FUNDER_WALLET_ADDRESS=0x_funder_wallet_address_here

# API credentials (auto-generated from agent private key)
CLOB_API_KEY=your_clob_api_key_here
CLOB_SECRET=your_clob_secret_here
CLOB_PASS_PHRASE=your_clob_passphrase_here
```

### Step 5: Generate API Credentials

Run a test to generate API credentials:

```python
from py_clob_client.client import ClobClient

# Initialize with agent wallet
client = ClobClient(
    host="https://clob.polymarket.com",
    key="0x_agent_private_key",
    chain_id=137,
    signature_type=1,  # Agent mode
    funder="0x_funder_address"
)

# Generate and display API credentials
creds = client.create_or_derive_api_creds()
print("API Key:", creds.api_key)
print("Secret:", creds.api_secret)
print("Passphrase:", creds.api_passphrase)
```

Add these to your `.env` file.

## 🧪 Testing Setup

### Test 1: Verify Agent Cannot Withdraw

```python
from common import get_clob_client

client = get_clob_client()
print("Client mode:", client.mode)  # Should show "agent-trading"

# Try to get balance (should work)
balance = client.get_balance()
print("Balance:", balance)

# Agent can place orders but cannot withdraw funds
# (withdrawals would require funder wallet signature)
```

### Test 2: Test Trading

```python
from common import get_clob_client

client = get_clob_client()

# Place a small test order
result = client.execute_market_order(
    token_id="your_test_token_id",
    side="buy",
    amount=1.0  # $1 test trade
)
print("Test order result:", result)
```

### Test 3: Verify Funder Control

```python
# This should fail - agent cannot withdraw
# Only funder wallet can withdraw funds
```

## 📁 Strategy-Specific Setup

### Copy Trading Strategy

```bash
cd strategy_copy_trading
cp .env.example .env
# Edit .env with agent + funder wallets
```

### Price Arbitrage Strategy

```bash
cd strategy_price_arbitrage
cp .env.example .env
# Edit .env with agent + funder wallets
```

### BTC Prediction Strategy

```bash
cd strategy_btc_price_prediction
cp .env.example .env
# Edit .env with agent + funder wallets
```

### Counter Trading Strategy

```bash
cd strategy_counter_trading
cp .env.example .env
# Edit .env with agent + funder wallets
```

## 🚀 Deployment

### Railway Deployment (Recommended)

Each strategy deploys independently:

```bash
cd strategy_copy_trading
railway init
railway link
railway variables set POLYGON_WALLET_PRIVATE_KEY=0x_agent_key
railway variables set FUNDER_WALLET_ADDRESS=0x_funder_address
railway variables set CLOB_API_KEY=your_api_key
railway variables set CLOB_SECRET=your_secret
railway variables set CLOB_PASS_PHRASE=your_passphrase
railway up
```

### Local Development

```bash
cd strategy_copy_trading
cp .env.example .env
# Edit .env with real values
python main.py
```

## 🔒 Security Best Practices

### Funder Wallet Security

- ✅ **Hardware wallet** (Ledger/Trezor) for funder
- ✅ **Multi-signature** setup for large amounts
- ✅ **Cold storage** for long-term holdings
- ✅ **Never expose funder private key**

### Agent Wallet Security

- ✅ **Unique agent per strategy**
- ✅ **Regular rotation** (create new agents periodically)
- ✅ **Monitor activity** closely
- ✅ **Small position limits** per agent

### Monitoring

- ✅ **Log all agent activity**
- ✅ **Set up alerts** for unusual trading
- ✅ **Regular balance checks**
- ✅ **Audit trails** for all transactions

## 🆘 Troubleshooting

### "Insufficient allowance" error

**Fix**: Set token allowances from funder wallet (not agent)

### "Invalid signature" error

**Fix**: Verify agent private key and funder address are correct

### Orders not executing

**Fix**: Check that funder wallet has sufficient USDC balance

### Cannot derive API credentials

**Fix**: Ensure agent private key is valid and funder address is set

## 📊 Cost Analysis

- **Agent Wallets**: Free to create
- **Gas Fees**: Only for allowance setup (one-time)
- **Trading Fees**: Standard Polymarket fees
- **Railway**: $5/month per deployed strategy

## 🎯 Benefits

- ✅ **Enhanced Security**: Funds isolated from trading logic
- ✅ **Risk Management**: Separate wallets per strategy
- ✅ **Easy Recovery**: Replace agent wallet without moving funds
- ✅ **Compliance**: Clear separation of trading vs custody
- ✅ **Scalability**: Deploy multiple strategies independently

---

**Ready to set up?** Create your agent and funder wallets, then configure each strategy's `.env` file! 🔐
