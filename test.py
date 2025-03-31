from typing import Any
import httpx
from decimal import Decimal
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("crypto")

# Constants
COINGECKO_API = "https://api.coingecko.com/api/v3"
SUPPORTED_CURRENCIES = ["usd", "eur", "gbp", "jpy"]

async def fetch_crypto_data(url: str) -> dict[str, Any] | None:
    """Make a request to the CoinGecko API with error handling."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_price_data(data: dict, coin_id: str, currency: str) -> str:
    """Format cryptocurrency price data into readable string."""
    coin_data = data.get(coin_id, {})
    if not coin_data:
        return f"No data available for {coin_id}"
    
    price = coin_data.get(currency, 0)
    change_24h = coin_data.get(f"{currency}_24h_change", 0)
    market_cap = coin_data.get(f"{currency}_market_cap", 0)
    
    return f"""
💰 {coin_id.upper()} Price Data:
Price: {currency.upper()} {price:,.2f}
24h Change: {change_24h:,.2f}%
Market Cap: {currency.upper()} {market_cap:,.0f}
"""

@mcp.tool()
async def get_price(coin_id: str, currency: str = "usd") -> str:
    """Get current price and details for a cryptocurrency.

    Args:
        coin_id: Cryptocurrency ID (e.g., bitcoin, ethereum, dogecoin)
        currency: Currency for price (default: usd)
    """
    currency = currency.lower()
    if currency not in SUPPORTED_CURRENCIES:
        return f"Unsupported currency. Please use one of: {', '.join(SUPPORTED_CURRENCIES)}"

    url = f"{COINGECKO_API}/simple/price"
    params = {
        "ids": coin_id.lower(),
        "vs_currencies": currency,
        "include_24hr_change": "true",
        "include_market_cap": "true"
    }
    
    query = "&".join(f"{k}={v}" for k, v in params.items())
    data = await fetch_crypto_data(f"{url}?{query}")

    if not data:
        return "Unable to fetch cryptocurrency data. Please try again later."

    return format_price_data(data, coin_id.lower(), currency)

@mcp.tool()
async def get_trending() -> str:
    """Get list of trending cryptocurrencies."""
    url = f"{COINGECKO_API}/search/trending"
    data = await fetch_crypto_data(url)

    if not data or "coins" not in data:
        return "Unable to fetch trending cryptocurrencies."

    trending = []
    for coin in data["coins"][:7]:  # Top 7 trending
        item = coin["item"]
        trending.append(f"""
🔥 {item['name']} ({item['symbol'].upper()})
Market Cap Rank: #{item.get('market_cap_rank', 'N/A')}
Price BTC: {item.get('price_btc', 0):.8f} BTC
""")

    return "\n---\n".join(trending)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')