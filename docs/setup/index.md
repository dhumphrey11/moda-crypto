# Setup Scripts and Tools

This directory contains setup scripts and tools for initializing and managing the Moda Crypto platform.

## 📁 Files Overview

### 🐍 `populate_watchlist.py`
**Main watchlist population script**
- Adds top 40 cryptocurrencies to Firestore watchlist
- Fetches real-time market data from CoinGecko API
- Supports dry-run and force modes
- Comprehensive error handling and progress reporting

### 🔧 `populate_watchlist.sh` 
**Bash wrapper script**
- Easy-to-use command-line interface
- Automatic dependency management
- Prerequisites checking
- Colored output and user confirmations

### ⚙️ `watchlist_config.ini`
**Configuration file**
- Customizable token lists
- API settings and rate limits
- Script behavior options
- Easy modification without code changes

### 📖 `README.md`
**Comprehensive documentation**
- Detailed usage instructions
- Prerequisites and setup guide
- Token list reference
- Troubleshooting tips

## 🚀 Quick Start

### Option 1: Using the Bash Wrapper (Recommended)
```bash
# Preview what would be added (dry run)
./docs/setup/populate_watchlist.sh --dry-run

# Add tokens to watchlist
./docs/setup/populate_watchlist.sh

# Force update existing tokens
./docs/setup/populate_watchlist.sh --force
```

### Option 2: Using Python Script Directly
```bash
# From project root
python docs/setup/populate_watchlist.py --dry-run
python docs/setup/populate_watchlist.py
```

## 📋 Prerequisites Checklist

- [ ] Backend dependencies installed (`pip install -r backend/requirements.txt`)
- [ ] Firebase credentials configured in `backend/.env`
- [ ] Internet connection for CoinGecko API
- [ ] Python 3.7+ available

## 🎯 What This Does

1. **Connects** to your Firestore database
2. **Fetches** current market data from CoinGecko API
3. **Adds** top 40 cryptocurrencies to your watchlist
4. **Includes** market cap, volume, and price data
5. **Reports** detailed progress and results

## 🔧 Customization

### Adding Custom Tokens
Edit `watchlist_config.ini` to include your preferred tokens:

```ini
[custom_tokens]
custom_list = [
    "SYMBOL,Token Name,coingecko-id",
    "MYTOKEN,My Token,my-token-id"
]
```

### Modifying the Script
The Python script includes these customizable sections:
- `TOP_40_CRYPTOS` tuple for token list
- API rate limiting settings
- Firestore collection names
- Market data fields to fetch

## 📊 Expected Results

After running the script successfully, your Firestore `tokens` collection will contain:

- 40 cryptocurrency tokens (or fewer if some already exist)
- Real-time market data for each token
- Properly formatted documents ready for the Moda Crypto platform

## 🛟 Need Help?

1. **Check the README**: Detailed troubleshooting guide included
2. **Run dry-run first**: Always preview changes before applying
3. **Verify prerequisites**: Ensure all requirements are met
4. **Check logs**: Script provides detailed error messages

## 🔒 Security Notes

- Script only **adds** data (no deletions)
- Uses public CoinGecko API (no API key required)
- Respects rate limits to avoid being blocked
- Firebase credentials remain secure in your `.env` file

---

For more information about the Moda Crypto platform, see the main [project README](../../README.md).