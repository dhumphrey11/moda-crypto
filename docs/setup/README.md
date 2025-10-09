# Watchlist Population Script

This directory contains scripts and tools for setting up and managing the Moda Crypto watchlist in Firestore.

## populate_watchlist.py

A comprehensive script to add the top 40 most popular cryptocurrencies to the Firestore watchlist with current market data from CoinGecko.

### Features

- ✅ Adds top 40 cryptocurrencies by market cap
- 📊 Fetches real-time market data from CoinGecko API
- 🔍 Dry-run mode to preview changes
- ⚠️ Force mode to overwrite existing tokens
- 🛡️ Error handling and rate limiting
- 📋 Detailed progress reporting

### Prerequisites

1. **Backend Setup**: Ensure the backend is properly configured
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Firebase Configuration**: Make sure Firebase credentials are set up in `backend/.env`:
   ```env
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_CLIENT_EMAIL=your-service-account-email
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
   ```

3. **Internet Connection**: Required for CoinGecko API calls

### Usage

#### Basic Usage (Dry Run)
Preview what tokens would be added without making changes:
```bash
cd /path/to/moda-crypto
python docs/setup/populate_watchlist.py --dry-run
```

#### Add Tokens to Watchlist
Add the top 40 cryptocurrencies to your watchlist:
```bash
cd /path/to/moda-crypto
python docs/setup/populate_watchlist.py
```

#### Force Update Existing Tokens
Overwrite existing tokens with fresh market data:
```bash
cd /path/to/moda-crypto
python docs/setup/populate_watchlist.py --force
```

#### Help
View all available options:
```bash
python docs/setup/populate_watchlist.py --help
```

### Token List

The script includes these top 40 cryptocurrencies:

| Symbol | Name | CoinGecko ID |
|--------|------|--------------|
| BTC | Bitcoin | bitcoin |
| ETH | Ethereum | ethereum |
| USDT | Tether | tether |
| BNB | BNB | binancecoin |
| SOL | Solana | solana |
| USDC | USD Coin | usd-coin |
| XRP | Ripple | ripple |
| DOGE | Dogecoin | dogecoin |
| TON | Toncoin | the-open-network |
| ADA | Cardano | cardano |
| SHIB | Shiba Inu | shiba-inu |
| AVAX | Avalanche | avalanche-2 |
| TRX | TRON | tron |
| DOT | Polkadot | polkadot |
| BCH | Bitcoin Cash | bitcoin-cash |
| LINK | Chainlink | chainlink |
| NEAR | NEAR Protocol | near |
| MATIC | Polygon | matic-network |
| ICP | Internet Computer | internet-computer |
| UNI | Uniswap | uniswap |
| LTC | Litecoin | litecoin |
| PEPE | Pepe | pepe |
| LEO | LEO Token | leo-token |
| DAI | Dai | dai |
| ETC | Ethereum Classic | ethereum-classic |
| HBAR | Hedera | hedera-hashgraph |
| XMR | Monero | monero |
| RENDER | Render Token | render-token |
| KASPA | Kaspa | kaspa |
| ARB | Arbitrum | arbitrum |
| VET | VeChain | vechain |
| XLM | Stellar | stellar |
| FIL | Filecoin | filecoin |
| ATOM | Cosmos | cosmos |
| CRO | Cronos | crypto-com-chain |
| MKR | Maker | maker |
| OP | Optimism | optimism |
| IMX | Immutable X | immutable-x |
| INJ | Injective | injective-protocol |
| MANTLE | Mantle | mantle |

### Data Structure

Each token is stored in Firestore with the following structure:

```json
{
  "symbol": "BTC",
  "name": "Bitcoin",
  "coingecko_id": "bitcoin",
  "active": true,
  "last_updated": "2025-10-09T12:00:00Z",
  "market_cap": 1234567890123,
  "liquidity_24h": 12345678901,
  "price_usd": 67890.12,
  "created_by": "populate_watchlist_script",
  "created_at": "2025-10-09T12:00:00Z"
}
```

### Error Handling

The script includes comprehensive error handling:

- **Connection Errors**: Gracefully handles Firestore connection issues
- **API Rate Limits**: Implements proper rate limiting for CoinGecko API
- **Missing Data**: Continues operation even if some market data is unavailable
- **Validation**: Ensures all required fields are present before adding tokens

### Rate Limiting

The script respects CoinGecko's API rate limits:
- Free tier: 50 calls per minute
- 1.5 second delay between requests
- Batches requests for efficiency

### Output Examples

#### Dry Run Output
```
🚀 Moda Crypto Watchlist Populator
==================================================
🔍 DRY RUN MODE - No changes will be made
📊 Preparing to add 40 cryptocurrencies

✓ Firestore connection established
Fetching market data from CoinGecko...
✓ Fetched market data for 40 tokens
Found 5 existing tokens in watchlist

============================================================
TOKEN    NAME                 STATUS       ACTION
============================================================
BTC      Bitcoin              EXISTS       Skipped
ETH      Ethereum             EXISTS       Skipped
SOL      Solana               WOULD ADD    Dry run
DOGE     Dogecoin             WOULD ADD    Dry run
...
```

#### Actual Run Output
```
🚀 Moda Crypto Watchlist Populator
==================================================
📊 Preparing to add 40 cryptocurrencies

✓ Firestore connection established
Fetching market data from CoinGecko...
✓ Fetched market data for 40 tokens
Found 5 existing tokens in watchlist

============================================================
TOKEN    NAME                 STATUS       ACTION
============================================================
BTC      Bitcoin              EXISTS       Skipped
ETH      Ethereum             EXISTS       Skipped
SOL      Solana               ADDED        Success
DOGE     Dogecoin             ADDED        Success
...

============================================================
📋 SUMMARY
============================================================
✅ Added: 35
🔄 Updated: 0
⏭️ Skipped: 5
❌ Failed: 0
📊 Total Processed: 40
```

### Troubleshooting

#### Firebase Connection Issues
```bash
# Check if .env file exists and has required variables
cat backend/.env | grep FIREBASE

# Test Firebase connection
cd backend
python -c "from app.firestore_client import init_db; db = init_db(); print('Connection successful')"
```

#### CoinGecko API Issues
- Check internet connection
- Verify CoinGecko API is accessible
- Rate limiting may cause delays (this is normal)

#### Import Errors
```bash
# Make sure backend dependencies are installed
cd backend
pip install -r requirements.txt

# Run from project root directory
cd /path/to/moda-crypto
python docs/setup/populate_watchlist.py
```

### Customization

To modify the token list, edit the `TOP_40_CRYPTOS` tuple in the script:

```python
TOP_40_CRYPTOS = [
    ("SYMBOL", "Token Name", "coingecko_id"),
    # Add your custom tokens here
]
```

### Security Notes

- The script only adds data to Firestore (no deletions)
- Market data is fetched from public CoinGecko API
- Firebase credentials should be properly secured
- Run with `--dry-run` first to preview changes

---

For more information about Moda Crypto, see the main [README.md](../../README.md).