# Alpha Vantage MCP Server

The official Alpha Vantage API MCP server enables LLMs and agentic workflows to seamlessly interact with real-time and historical stock market data through the Model Context Protocol (MCP). Add this server to your favorite apps such as Claude, Claude Code, Cursor, VS Code, and many more to give them access to comprehensive financial data.

## Quickstart

To use the server, <a href="https://www.alphavantage.co/support/#api-key" onclick="gtag('event', 'mcp_getKey')">get your free Alpha Vantage API key</a>, copy it to your clipboard, then follow the instructions below for the agentic tool/platform of your interest.

👉 Any questions? Please contact support@alphavantage.co

⭐ View MCP source code on [Github](https://github.com/alphavantage/alpha_vantage_mcp)


### Connection Examples

**Remote Server Connection:**
```
https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY
```

**Local Server Connection:**
```
uvx av-mcp YOUR_API_KEY
```

&nbsp;

### Platform Setup Instructions by Use Case
💬📊 _Power your chatbot with financial data_


<details>
<summary><b>Install in Claude</b></summary>

**Requirements:**
- Claude Pro account (or higher tier)
  
#### Claude Remote Server Connection

To connect Claude (Web or Desktop) to this MCP server:

📺 Watch the **setup tutorial** - Click the image below to watch a step-by-step video guide:

[![Alpha Vantage MCP Setup Tutorial](https://img.youtube.com/vi/W69x2qJcYmI/maxresdefault.jpg)](https://www.youtube.com/watch?v=W69x2qJcYmI)


📺 Already have your Alpha Vantage MCP server set up? Below are a few examples of Claude performing various stock analysis & charting tasks:

[![Alpha Vantage MCP Example Prompts](https://img.youtube.com/vi/tyl9E7fddvU/maxresdefault.jpg)](https://www.youtube.com/watch?v=tyl9E7fddvU)

**Query Param Option (Recommended):**
1. Go to [claude.ai/settings/connectors](https://claude.ai/settings/connectors) (Web) or Settings → Connectors (Desktop)
2. Click "Add Custom Connector"
3. Add the MCP server URL with your API key: `https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY` (replace `YOUR_API_KEY` with your actual Alpha Vantage API key)
4. Click "Connect"

**OAuth Option:**
1. Go to [claude.ai/settings/connectors](https://claude.ai/settings/connectors) (Web) or Settings → Connectors (Desktop)
2. Click "Add Custom Connector"
3. Add the MCP server URL: `https://mcp.alphavantage.co/mcp`
4. Click "Connect"
5. Enter your Alpha Vantage API token
6. Click "Authorize Access"

#### Claude Local Server Connection
See [Claude Desktop MCP docs](https://modelcontextprotocol.io/quickstart/user) for more info.

Install `uv` (a [modern Python package](https://docs.astral.sh/uv/) and project manager):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Open Claude Desktop developer settings and edit your `claude_desktop_config.json` file to add the following configuration:

```json
{
  "mcpServers": {
    "alphavantage": {
      "command": "uvx",
      "args": ["av-mcp", "YOUR_API_KEY"]
    }
  }
}
```

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

</details>


<details>
<summary><b>Install in ChatGPT</b></summary>

**Requirements:**
- ChatGPT Plus account (or higher tier)
- Developer mode enabled (beta feature) - see [OpenAI's Developer Mode documentation](https://platform.openai.com/docs/guides/developer-mode)
  
To connect ChatGPT to this MCP server using ChatGPT Developer mode:

**Setup:**
1. Go to [ChatGPT Settings → Connectors](https://chatgpt.com/#settings/Connectors)
2. Enable **Advanced → Developer mode**
3. Add a remote MCP server with URL: `https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY` (replace `YOUR_API_KEY` with your actual Alpha Vantage API key)
4. In conversations, choose **Developer mode** from the Plus menu and select the Alpha Vantage connector

**Note:** While Developer mode is available for both Pro and Plus accounts, MCP tool execution is currently most reliable with Pro accounts. We're monitoring Plus plan functionality and will update this guide as improvements are made.

</details>

&nbsp;

💻💵 _Code up fintech apps_

<details>
<summary><b>Install in OpenAI Codex</b></summary>

**Requirements:**
- ChatGPT Plus account (or higher tier)

See [OpenAI Codex](https://github.com/openai/codex) for more information.

Install `uv` (a [modern Python package](https://docs.astral.sh/uv/) and project manager):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install **Codex CLI v0.34 or later** to avoid compatibility issues.

```bash
# Install (if not already installed)
npm install -g @openai/codex

# Or update to the latest version
npm update -g @openai/codex

# Verify installation and version
codex --version
```

Add the following configuration to your Codex MCP server settings by editing `~/.codex/config.toml`:

```toml
[mcp_servers.alphavantage]
command = "uvx"
args = ["av-mcp", "YOUR_API_KEY"]
```

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

Run `codex` in your terminal from your project directory. First-time users will be guided through additional prompts.

Then connect with:
```
/mcp
```

</details>

<details>
<summary><b>Install in Visual Studio Code</b></summary>

See [VS Code MCP docs](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) for more info.

Create `.vscode/mcp.json` (your VS Code MCP config file) in your workspace, and paste into it one of the following configurations, depending on whether you’re connecting remotely or running the server locally.

#### VS Code Remote Server Connection

Paste the following into `.vscode/mcp.json`:

```json
{
  "servers": {
    "alphavantage": {
      "type": "http",
      "url": "https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY"
    }
  }
}
```

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

#### VS Code Local Server Connection

First, install `uv` (a [modern Python package](https://docs.astral.sh/uv/) and project manager):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, paste the following into `.vscode/mcp.json`:

```json
{
  "servers": {
    "alphavantage": {
      "type": "stdio",
      "command": "uvx",
      "args": ["av-mcp", "YOUR_API_KEY"]
    }
  }
}
```

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

Open the Chat view and select Agent mode

</details>


<details>
<summary><b>Install in Cursor</b></summary>

See [Cursor MCP docs](https://docs.cursor.com/context/model-context-protocol) for more information.

Paste one of the following configurations into your Cursor `~/.cursor/mcp.json` file, depending on whether you’re connecting remotely or running the server locally. You may also install in a specific project by creating `.cursor/mcp.json` in your project folder. 

#### Cursor Remote Server Connection

Configure Cursor by editing `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "alphavantage": {
      "url": "https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY"
    }
  }
}
```

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

#### Cursor Local Server Connection

First, install `uv` (a [modern Python package](https://docs.astral.sh/uv/) and project manager):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, paste the following into your Cursor `~/.cursor/mcp.json` file:

```json
{
  "mcpServers": {
    "alphavantage": {
      "command": "uvx",
      "args": ["av-mcp", "YOUR_API_KEY"]
    }
  }
}
```

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

</details>


<details>
<summary><b>Install in Claude Code</b></summary>

  **Requirements:**
- Claude Pro account (or higher tier)
  
See [Claude Code MCP docs](https://docs.anthropic.com/en/docs/claude-code/mcp) for more information.

Run one of the following commands, depending on whether you’re connecting remotely or running the server locally.

#### Claude Code Remote Server Connection

```bash
claude mcp add -t http alphavantage https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY
```

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

#### Claude Code Local Server Connection

First, install `uv` (a [modern Python package](https://docs.astral.sh/uv/) and project manager):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then run:

```bash
claude mcp add alphavantage -- uvx av-mcp YOUR_API_KEY
```

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

Run `claude` in your terminal from your project directory.

Then connect with:
```
/mcp
```

</details>



<details>
<summary><b>Install in Gemini CLI</b></summary>

See [Gemini CLI Configuration](https://google-gemini.github.io/gemini-cli/docs/tools/mcp-server.html) for more information.

Run one of the following commands, depending on whether you’re connecting remotely or running the server locally.

**Gemini CLI Remote Server Connection (Recommended):**
```bash
gemini mcp add -t http alphavantage https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY
```

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

**Gemini CLI Local Server Connection:**

Install `uv` (a [modern Python package](https://docs.astral.sh/uv/) and project manager):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then run:

```bash
gemini mcp add alphavantage uvx av-mcp YOUR_API_KEY
```

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

**Manual Configuration:**
1. Open the Gemini CLI settings file. The location is `~/.gemini/settings.json` (where `~` is your home directory).
2. Add the following to the `mcpServers` object in your `settings.json` file (replace `YOUR_API_KEY` with your actual Alpha Vantage API key):

```json
{
  "mcpServers": {
    "alphavantage": {
      "httpUrl": "https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY"
    }
  }
}
```

Or, for a local server (replace `YOUR_API_KEY` with your actual Alpha Vantage API key):

```json
{
  "mcpServers": {
    "alphavantage": {
      "command": "uvx",
      "args": ["av-mcp", "YOUR_API_KEY"]
    }
  }
}
```

If the `mcpServers` object does not exist, create it.

</details>

&nbsp;

🤖📈 _Create agentic workflows for quantitative investing_

<details>
<summary><b>Install in OpenAI Agents SDK</b></summary>

To use the Alpha Vantage MCP server with OpenAI Agents SDK, see our [example agent](https://github.com/alphavantage/alpha_vantage_mcp/blob/main/examples/agent/README.md) that demonstrates:

- Interactive financial analysis agent
- Session management for conversation continuity
- Real-time tool execution with Alpha Vantage data
- Support for both HTTP and stdio MCP connections

The example includes a complete setup guide and configuration templates.

</details>

&nbsp;

### Category Filtering
Optionally filter available tools by category using:
- **Query parameter**: `?categories=core_stock_apis,alpha_intelligence`

Available categories:
- `core_stock_apis` - Core stock market data APIs
- `options_data_apis` - Options data APIs  
- `alpha_intelligence` - News sentiment and intelligence APIs
- `fundamental_data` - Company fundamentals and financial data
- `forex` - Foreign exchange rates and data
- `cryptocurrencies` - Digital and crypto currencies data
- `commodities` - Commodities and precious metals data
- `economic_indicators` - Economic indicators and market data
- `technical_indicators` - Technical analysis indicators and calculations
- `ping` - Health check and utility tools

If no categories are specified, all tools will be available.

&nbsp;

## Tools Reference

| Category | Tools |
|----------|-------|
| core_stock_apis | `GET_TIME_SERIES` *(consolidated)*, `TIME_SERIES_INTRADAY`, `TIME_SERIES_DAILY`, `TIME_SERIES_DAILY_ADJUSTED`, `TIME_SERIES_WEEKLY`, `TIME_SERIES_WEEKLY_ADJUSTED`, `TIME_SERIES_MONTHLY`, `TIME_SERIES_MONTHLY_ADJUSTED`, `GLOBAL_QUOTE`, `REALTIME_BULK_QUOTES`, `SYMBOL_SEARCH`, `MARKET_STATUS` |
| options_data_apis | `REALTIME_OPTIONS`, `HISTORICAL_OPTIONS` |
| alpha_intelligence | `NEWS_SENTIMENT`, `EARNINGS_CALL_TRANSCRIPT`, `TOP_GAINERS_LOSERS`, `INSIDER_TRANSACTIONS`, `ANALYTICS_FIXED_WINDOW`, `ANALYTICS_SLIDING_WINDOW` |
| fundamental_data | `COMPANY_OVERVIEW`, `INCOME_STATEMENT`, `BALANCE_SHEET`, `CASH_FLOW`, `EARNINGS`, `LISTING_STATUS`, `EARNINGS_CALENDAR`, `IPO_CALENDAR` |
| forex | `GET_FOREX_DATA` *(consolidated)*, `FX_INTRADAY`, `FX_DAILY`, `FX_WEEKLY`, `FX_MONTHLY` |
| cryptocurrencies | `GET_CRYPTO_DATA` *(consolidated)*, `CURRENCY_EXCHANGE_RATE`, `CRYPTO_INTRADAY`, `DIGITAL_CURRENCY_DAILY`, `DIGITAL_CURRENCY_WEEKLY`, `DIGITAL_CURRENCY_MONTHLY` |
| commodities | `WTI`, `BRENT`, `NATURAL_GAS`, `COPPER`, `ALUMINUM`, `WHEAT`, `CORN`, `COTTON`, `SUGAR`, `COFFEE`, `ALL_COMMODITIES` |
| economic_indicators | `REAL_GDP`, `REAL_GDP_PER_CAPITA`, `TREASURY_YIELD`, `FEDERAL_FUNDS_RATE`, `CPI`, `INFLATION`, `RETAIL_SALES`, `DURABLES`, `UNEMPLOYMENT`, `NONFARM_PAYROLL` |
| technical_indicators | `GET_MOVING_AVERAGE` *(consolidated)*, `SMA`, `EMA`, `WMA`, `DEMA`, `TEMA`, `TRIMA`, `KAMA`, `MAMA`, `VWAP`, `T3`, `MACD`, `MACDEXT`, `STOCH`, `STOCHF`, `RSI`, `STOCHRSI`, `WILLR`, `ADX`, `ADXR`, `APO`, `PPO`, `MOM`, `BOP`, `CCI`, `CMO`, `ROC`, `ROCR`, `AROON`, `AROONOSC`, `MFI`, `TRIX`, `ULTOSC`, `DX`, `MINUS_DI`, `PLUS_DI`, `MINUS_DM`, `PLUS_DM`, `BBANDS`, `MIDPOINT`, `MIDPRICE`, `SAR`, `TRANGE`, `ATR`, `NATR`, `AD`, `ADOSC`, `OBV`, `HT_TRENDLINE`, `HT_SINE`, `HT_TRENDMODE`, `HT_DCPERIOD`, `HT_DCPHASE`, `HT_PHASOR` |
| ping | `PING`, `ADD_TWO_NUMBERS` |

&nbsp;

### Table of Contents - API Tools
- [🎯 GET_TIME_SERIES - Unified Time Series Tool](#-get_time_series---unified-time-series-tool) *(NEW - Consolidates 11 tools)*
- [💱 GET_FOREX_DATA - Unified Forex Tool](#-get_forex_data---unified-forex-tool) *(NEW - Consolidates 4 tools)*
- [₿ GET_CRYPTO_DATA - Unified Crypto Tool](#-get_crypto_data---unified-crypto-tool) *(NEW - Consolidates 5 tools)*
- [📈 GET_MOVING_AVERAGE - Unified Moving Average Tool](#-get_moving_average---unified-moving-average-tool) *(NEW - Consolidates 10 tools)*
- [core_stock_apis](#core_stock_apis)
- [options_data_apis](#options_data_apis)
- [alpha_intelligence](#alpha_intelligence)
- [fundamental_data](#fundamental_data)
- [forex](#forex)
- [cryptocurrencies](#cryptocurrencies)
- [commodities](#commodities)
- [economic_indicators](#economic_indicators)
- [technical_indicators](#technical_indicators)
- [ping](#ping)

💡 Each of these MCP tools maps to a corresponding Alpha Vantage API endpoint. If you are interested in the full API specs (in addition to the brief tool descriptions below), please refer to the Alpha Vantage [API documentation](https://www.alphavantage.co/documentation/).

---

## 🎯 GET_TIME_SERIES - Unified Time Series Tool

**NEW:** Consolidates 11 separate time series tools into one unified interface with ~85% context window reduction.

### Overview

`GET_TIME_SERIES` is a powerful consolidated tool that replaces 11 individual time series endpoints with a single, easy-to-use interface. Simply specify the `series_type` parameter to access any time series data.

**Key Benefits:**
- ✅ One tool instead of 11 (simpler API, less to remember)
- ✅ ~7,000 token reduction in context window usage
- ✅ Consistent parameter validation across all series types
- ✅ Automatic large response handling via output helper
- ✅ Clear error messages when parameters don't match series type

### Supported Series Types

| series_type | Description | Replaces Tool |
|-------------|-------------|---------------|
| `intraday` | Intraday OHLCV data (1min-60min bars) | TIME_SERIES_INTRADAY |
| `daily` | Raw daily OHLCV data | TIME_SERIES_DAILY |
| `daily_adjusted` | Daily data with split/dividend adjustments | TIME_SERIES_DAILY_ADJUSTED |
| `weekly` | Weekly time series (last day of week) | TIME_SERIES_WEEKLY |
| `weekly_adjusted` | Adjusted weekly time series | TIME_SERIES_WEEKLY_ADJUSTED |
| `monthly` | Monthly time series (last day of month) | TIME_SERIES_MONTHLY |
| `monthly_adjusted` | Adjusted monthly time series | TIME_SERIES_MONTHLY_ADJUSTED |
| `quote` | Latest price and volume for a symbol | GLOBAL_QUOTE |
| `bulk_quotes` | Real-time quotes for up to 100 symbols | REALTIME_BULK_QUOTES |
| `search` | Symbol search/lookup by keywords | SYMBOL_SEARCH |
| `market_status` | Current market status (open/closed) | MARKET_STATUS |

### Parameters

**Required Parameters (vary by series_type):**

| series_type | Required Parameters | Optional Parameters |
|-------------|-------------------|---------------------|
| `intraday` | `symbol`, `interval` | `adjusted`, `extended_hours`, `month`, `outputsize` |
| `daily`, `daily_adjusted` | `symbol` | `outputsize` |
| `weekly`, `weekly_adjusted`, `monthly`, `monthly_adjusted` | `symbol` | None |
| `quote` | `symbol` | None |
| `bulk_quotes` | `symbols` | None |
| `search` | `keywords` | None |
| `market_status` | None | None |

**Common Parameters (all series types):**
- `datatype`: Output format (`"json"` or `"csv"`, default: `"csv"`)
- `entitlement`: Data entitlement level (`"delayed"` or `"realtime"`)
- `force_inline`: Force inline output regardless of size (default: `false`)
- `force_file`: Force file output regardless of size (default: `false`)

**Intraday-Specific Parameters:**
- `interval`: Time interval - `"1min"`, `"5min"`, `"15min"`, `"30min"`, `"60min"`
- `adjusted`: Return adjusted data (default: `true`)
- `extended_hours`: Include extended trading hours (default: `true`)
- `month`: Query specific month in `YYYY-MM` format (e.g., `"2024-01"`)
- `outputsize`: `"compact"` (latest 100 points) or `"full"` (complete history)

### Usage Examples

**1. Get Intraday Data for IBM:**
```python
GET_TIME_SERIES(
    series_type="intraday",
    symbol="IBM",
    interval="5min",
    outputsize="compact"
)
```

**2. Get Daily Adjusted Data for Apple:**
```python
GET_TIME_SERIES(
    series_type="daily_adjusted",
    symbol="AAPL",
    outputsize="full"
)
```

**3. Get Real-Time Quotes for Multiple Stocks:**
```python
GET_TIME_SERIES(
    series_type="bulk_quotes",
    symbols="AAPL,MSFT,GOOGL,TSLA"
)
```

**4. Search for a Symbol:**
```python
GET_TIME_SERIES(
    series_type="search",
    keywords="microsoft"
)
```

**5. Check Market Status:**
```python
GET_TIME_SERIES(
    series_type="market_status"
)
```

**6. Get Historical Monthly Data:**
```python
GET_TIME_SERIES(
    series_type="monthly_adjusted",
    symbol="NVDA"
)
```

### Migration from Old Tools

If you were using the individual tools, here's how to migrate:

**Old approach:**
```python
TIME_SERIES_INTRADAY(symbol="IBM", interval="5min")
TIME_SERIES_DAILY_ADJUSTED(symbol="AAPL")
REALTIME_BULK_QUOTES(symbol="AAPL,MSFT")  # Note: misleading parameter name
SYMBOL_SEARCH(keywords="microsoft")
```

**New approach:**
```python
GET_TIME_SERIES(series_type="intraday", symbol="IBM", interval="5min")
GET_TIME_SERIES(series_type="daily_adjusted", symbol="AAPL")
GET_TIME_SERIES(series_type="bulk_quotes", symbols="AAPL,MSFT")  # Clearer parameter name
GET_TIME_SERIES(series_type="search", keywords="microsoft")
```

**Key Changes:**
- Add `series_type` parameter to specify data type
- For bulk quotes: use `symbols` instead of `symbol` (clearer intent)
- All other parameters remain the same

### Error Handling

The tool provides clear error messages when parameters don't match the series_type:

```python
# ❌ Wrong: Missing required parameter
GET_TIME_SERIES(series_type="intraday", symbol="IBM")
# Error: "interval is required when series_type='intraday'"

# ❌ Wrong: Using wrong parameter
GET_TIME_SERIES(series_type="bulk_quotes", symbol="AAPL")
# Error: "Use 'symbols' (not 'symbol') parameter for series_type='bulk_quotes'"

# ✅ Correct
GET_TIME_SERIES(series_type="intraday", symbol="IBM", interval="5min")
GET_TIME_SERIES(series_type="bulk_quotes", symbols="AAPL,MSFT")
```

---

## 💱 GET_FOREX_DATA - Unified Forex Tool

**NEW:** Consolidates 4 separate forex tools into one unified interface with ~78% context window reduction.

### Overview

`GET_FOREX_DATA` is a consolidated tool that replaces 4 individual forex endpoints with a single, easy-to-use interface. Simply specify the `timeframe` parameter to access any forex data.

**Key Benefits:**
- ✅ One tool instead of 4 (simpler API, less to remember)
- ✅ ~2,400 token reduction in context window usage
- ✅ Consistent parameter validation across all timeframes
- ✅ Clear error messages when parameters don't match timeframe
- ✅ Support for all major forex currency pairs

### Supported Timeframes

| timeframe | Description | Replaces Tool |
|-----------|-------------|---------------|
| `intraday` | Intraday exchange rates (1min-60min bars) | FX_INTRADAY |
| `daily` | Daily exchange rates | FX_DAILY |
| `weekly` | Weekly exchange rates (last day of week) | FX_WEEKLY |
| `monthly` | Monthly exchange rates (last day of month) | FX_MONTHLY |

### Parameters

**Required Parameters (all timeframes):**
- `timeframe`: The timeframe for the data - `"intraday"`, `"daily"`, `"weekly"`, or `"monthly"`
- `from_symbol`: The currency to convert from (e.g., `"EUR"`, `"GBP"`, `"USD"`)
- `to_symbol`: The currency to convert to (e.g., `"USD"`, `"JPY"`, `"CHF"`)

**Timeframe-Specific Parameters:**

| timeframe | Additional Required | Optional Parameters |
|-----------|-------------------|---------------------|
| `intraday` | `interval` | `outputsize` |
| `daily`, `weekly`, `monthly` | None | `outputsize` |

**Common Optional Parameters:**
- `outputsize`: `"compact"` (latest 100 points) or `"full"` (complete history), default: `"compact"`
- `datatype`: Output format (`"json"` or `"csv"`, default: `"csv"`)
- `force_inline`: Force inline output regardless of size (default: `false`)
- `force_file`: Force file output regardless of size (default: `false`)

**Intraday-Specific Parameters:**
- `interval`: Time interval - `"1min"`, `"5min"`, `"15min"`, `"30min"`, `"60min"` (required for intraday)

### Usage Examples

**1. Get Intraday EUR/USD Exchange Rate:**
```python
GET_FOREX_DATA(
    timeframe="intraday",
    from_symbol="EUR",
    to_symbol="USD",
    interval="5min",
    outputsize="compact"
)
```

**2. Get Daily GBP/USD Exchange Rate (Full History):**
```python
GET_FOREX_DATA(
    timeframe="daily",
    from_symbol="GBP",
    to_symbol="USD",
    outputsize="full"
)
```

**3. Get Weekly EUR/JPY Exchange Rate:**
```python
GET_FOREX_DATA(
    timeframe="weekly",
    from_symbol="EUR",
    to_symbol="JPY"
)
```

**4. Get Monthly CAD/USD Exchange Rate:**
```python
GET_FOREX_DATA(
    timeframe="monthly",
    from_symbol="CAD",
    to_symbol="USD"
)
```

### Migration from Old Tools

If you were using the individual forex tools, here's how to migrate:

**Old approach:**
```python
FX_INTRADAY(from_symbol="EUR", to_symbol="USD", interval="5min")
FX_DAILY(from_symbol="GBP", to_symbol="USD", outputsize="full")
FX_WEEKLY(from_symbol="EUR", to_symbol="JPY")
FX_MONTHLY(from_symbol="CAD", to_symbol="USD")
```

**New approach:**
```python
GET_FOREX_DATA(timeframe="intraday", from_symbol="EUR", to_symbol="USD", interval="5min")
GET_FOREX_DATA(timeframe="daily", from_symbol="GBP", to_symbol="USD", outputsize="full")
GET_FOREX_DATA(timeframe="weekly", from_symbol="EUR", to_symbol="JPY")
GET_FOREX_DATA(timeframe="monthly", from_symbol="CAD", to_symbol="USD")
```

**Key Changes:**
- Add `timeframe` parameter to specify the data frequency
- All other parameters remain the same

### Error Handling

The tool provides clear error messages when parameters don't match the timeframe:

```python
# ❌ Wrong: Missing required interval for intraday
GET_FOREX_DATA(timeframe="intraday", from_symbol="EUR", to_symbol="USD")
# Error: "interval is required when timeframe='intraday'"

# ❌ Wrong: Using interval with non-intraday timeframe
GET_FOREX_DATA(timeframe="daily", from_symbol="EUR", to_symbol="USD", interval="5min")
# Error: "interval parameter is not applicable for timeframe='daily'"

# ✅ Correct
GET_FOREX_DATA(timeframe="intraday", from_symbol="EUR", to_symbol="USD", interval="5min")
GET_FOREX_DATA(timeframe="daily", from_symbol="EUR", to_symbol="USD")
```

---

## ₿ GET_CRYPTO_DATA - Unified Crypto Tool

**NEW:** Consolidates 5 separate cryptocurrency/currency tools into one unified interface with ~78% context window reduction.

### Overview

`GET_CRYPTO_DATA` is a powerful consolidated tool that replaces 5 individual crypto/currency endpoints with a single, easy-to-use interface. It handles both time series data and exchange rates through the `data_type` parameter.

**Key Benefits:**
- ✅ One tool instead of 5 (simpler API, less to remember)
- ✅ ~3,200 token reduction in context window usage
- ✅ Handles both crypto time series and exchange rates
- ✅ Consistent parameter validation across all data types
- ✅ Clear error messages when parameters don't match data type

### Supported Data Types

| data_type | timeframe | Description | Replaces Tool |
|-----------|-----------|-------------|---------------|
| `timeseries` | `intraday` | Intraday crypto time series (1min-60min) | CRYPTO_INTRADAY |
| `timeseries` | `daily` | Daily crypto time series | DIGITAL_CURRENCY_DAILY |
| `timeseries` | `weekly` | Weekly crypto time series | DIGITAL_CURRENCY_WEEKLY |
| `timeseries` | `monthly` | Monthly crypto time series | DIGITAL_CURRENCY_MONTHLY |
| `exchange_rate` | N/A | Real-time currency exchange rate | CURRENCY_EXCHANGE_RATE |

### Parameters

**Required Parameters (vary by data_type):**

| data_type | Required Parameters |
|-----------|-------------------|
| `timeseries` | `timeframe`, `symbol`, `market` |
| `exchange_rate` | `from_currency`, `to_currency` |

**Timeseries-Specific:**
- `symbol`: The cryptocurrency symbol (e.g., `"BTC"`, `"ETH"`, `"XRP"`)
- `market`: The market currency (e.g., `"USD"`, `"EUR"`, `"CNY"`)
- `timeframe`: `"intraday"`, `"daily"`, `"weekly"`, or `"monthly"`
- `interval`: Time interval for intraday only - `"1min"`, `"5min"`, `"15min"`, `"30min"`, `"60min"`

**Exchange Rate-Specific:**
- `from_currency`: The currency to convert from (crypto or fiat, e.g., `"BTC"`, `"USD"`)
- `to_currency`: The currency to convert to (crypto or fiat, e.g., `"USD"`, `"BTC"`)

**Common Optional Parameters:**
- `outputsize`: `"compact"` (latest 100 points) or `"full"` (complete history), default: `"compact"`
- `datatype`: Output format (`"json"` or `"csv"`, default: `"csv"`)
- `force_inline`: Force inline output regardless of size (default: `false`)
- `force_file`: Force file output regardless of size (default: `false`)

### Usage Examples

**1. Get Intraday BTC/USD Time Series:**
```python
GET_CRYPTO_DATA(
    data_type="timeseries",
    timeframe="intraday",
    symbol="BTC",
    market="USD",
    interval="5min",
    outputsize="compact"
)
```

**2. Get Daily ETH/USD Time Series:**
```python
GET_CRYPTO_DATA(
    data_type="timeseries",
    timeframe="daily",
    symbol="ETH",
    market="USD"
)
```

**3. Get Weekly XRP/EUR Time Series:**
```python
GET_CRYPTO_DATA(
    data_type="timeseries",
    timeframe="weekly",
    symbol="XRP",
    market="EUR"
)
```

**4. Get Monthly LTC/CNY Time Series:**
```python
GET_CRYPTO_DATA(
    data_type="timeseries",
    timeframe="monthly",
    symbol="LTC",
    market="CNY"
)
```

**5. Get BTC to USD Exchange Rate:**
```python
GET_CRYPTO_DATA(
    data_type="exchange_rate",
    from_currency="BTC",
    to_currency="USD"
)
```

**6. Get USD to BTC Exchange Rate (Fiat to Crypto):**
```python
GET_CRYPTO_DATA(
    data_type="exchange_rate",
    from_currency="USD",
    to_currency="BTC"
)
```

**7. Get Crypto-to-Crypto Exchange Rate:**
```python
GET_CRYPTO_DATA(
    data_type="exchange_rate",
    from_currency="BTC",
    to_currency="ETH"
)
```

### Migration from Old Tools

If you were using the individual crypto/currency tools, here's how to migrate:

**Old approach:**
```python
CRYPTO_INTRADAY(symbol="BTC", market="USD", interval="5min")
DIGITAL_CURRENCY_DAILY(symbol="ETH", market="USD")
DIGITAL_CURRENCY_WEEKLY(symbol="XRP", market="EUR")
DIGITAL_CURRENCY_MONTHLY(symbol="LTC", market="CNY")
CURRENCY_EXCHANGE_RATE(from_currency="BTC", to_currency="USD")
```

**New approach:**
```python
GET_CRYPTO_DATA(data_type="timeseries", timeframe="intraday", symbol="BTC", market="USD", interval="5min")
GET_CRYPTO_DATA(data_type="timeseries", timeframe="daily", symbol="ETH", market="USD")
GET_CRYPTO_DATA(data_type="timeseries", timeframe="weekly", symbol="XRP", market="EUR")
GET_CRYPTO_DATA(data_type="timeseries", timeframe="monthly", symbol="LTC", market="CNY")
GET_CRYPTO_DATA(data_type="exchange_rate", from_currency="BTC", to_currency="USD")
```

**Key Changes:**
- Add `data_type` parameter (`"timeseries"` or `"exchange_rate"`)
- For timeseries: add `timeframe` parameter
- All other parameters remain the same

### Error Handling

The tool provides clear error messages when parameters don't match the data type:

```python
# ❌ Wrong: Missing timeframe for timeseries
GET_CRYPTO_DATA(data_type="timeseries", symbol="BTC", market="USD")
# Error: "timeframe is required when data_type='timeseries'"

# ❌ Wrong: Missing interval for intraday timeseries
GET_CRYPTO_DATA(data_type="timeseries", timeframe="intraday", symbol="BTC", market="USD")
# Error: "interval is required when timeframe='intraday'"

# ❌ Wrong: Using timeseries params with exchange_rate
GET_CRYPTO_DATA(data_type="exchange_rate", from_currency="BTC", to_currency="USD", symbol="BTC")
# Error: "symbol/market parameters are only applicable for data_type='timeseries'"

# ✅ Correct
GET_CRYPTO_DATA(data_type="timeseries", timeframe="intraday", symbol="BTC", market="USD", interval="5min")
GET_CRYPTO_DATA(data_type="timeseries", timeframe="daily", symbol="BTC", market="USD")
GET_CRYPTO_DATA(data_type="exchange_rate", from_currency="BTC", to_currency="USD")
```

---

## 📈 GET_MOVING_AVERAGE - Unified Moving Average Tool

**NEW:** Consolidates 10 separate moving average indicator tools into one unified interface with ~90% context window reduction.

### Overview

`GET_MOVING_AVERAGE` is a powerful consolidated tool that replaces 10 individual moving average endpoints with a single, easy-to-use interface. Simply specify the `indicator_type` parameter to access any moving average indicator.

**Key Benefits:**
- ✅ One tool instead of 10 (simpler API, less to remember)
- ✅ ~5,400 token reduction in context window usage
- ✅ Sophisticated conditional validation for complex parameter patterns
- ✅ Clear error messages when parameters don't match indicator type
- ✅ Support for all major moving average types including adaptive algorithms

### Supported Indicator Types

| indicator_type | Description | Replaces Tool |
|----------------|-------------|---------------|
| `sma` | Simple Moving Average | SMA |
| `ema` | Exponential Moving Average | EMA |
| `wma` | Weighted Moving Average | WMA |
| `dema` | Double Exponential Moving Average | DEMA |
| `tema` | Triple Exponential Moving Average | TEMA |
| `trima` | Triangular Moving Average | TRIMA |
| `kama` | Kaufman Adaptive Moving Average | KAMA |
| `mama` | MESA Adaptive Moving Average | MAMA |
| `t3` | Triple Exponential Moving Average T3 | T3 |
| `vwap` | Volume Weighted Average Price | VWAP |

### Parameters

The tool uses sophisticated conditional validation to handle three distinct parameter patterns:

#### 1. Standard Indicators (SMA, EMA, WMA, DEMA, TEMA, TRIMA, KAMA, T3)

**Required Parameters:**
- `indicator_type`: One of `"sma"`, `"ema"`, `"wma"`, `"dema"`, `"tema"`, `"trima"`, `"kama"`, `"t3"`
- `symbol`: Stock ticker symbol (e.g., `"IBM"`, `"AAPL"`)
- `interval`: Time interval - `"1min"`, `"5min"`, `"15min"`, `"30min"`, `"60min"`, `"daily"`, `"weekly"`, `"monthly"`
- `time_period`: Number of data points for calculation (positive integer, e.g., `60`, `200`)
- `series_type`: Price type - `"close"`, `"open"`, `"high"`, `"low"`

**Optional Parameters:**
- `month`: Specific month for intraday data in `YYYY-MM` format (e.g., `"2024-01"`) - **only for intraday intervals**

#### 2. MAMA (MESA Adaptive Moving Average)

**Required Parameters:**
- `indicator_type`: `"mama"`
- `symbol`: Stock ticker symbol
- `interval`: Time interval (same options as standard indicators)
- `series_type`: Price type - `"close"`, `"open"`, `"high"`, `"low"`

**Optional Parameters:**
- `fastlimit`: Fast limit (0.0-1.0), default: `0.01`
- `slowlimit`: Slow limit (0.0-1.0), default: `0.01`
- `month`: Specific month for intraday data (intraday only)

**Note:** MAMA does NOT use `time_period` - it uses `fastlimit` and `slowlimit` instead.

#### 3. VWAP (Volume Weighted Average Price)

**Required Parameters:**
- `indicator_type`: `"vwap"`
- `symbol`: Stock ticker symbol
- `interval`: **Must be intraday** - `"1min"`, `"5min"`, `"15min"`, `"30min"`, `"60min"`

**Optional Parameters:**
- `month`: Specific month for intraday data in `YYYY-MM` format

**Note:** VWAP does NOT use `time_period` or `series_type` - it calculates from OHLCV data automatically.

#### Common Optional Parameters (All Indicators)

- `datatype`: Output format (`"json"` or `"csv"`, default: `"csv"`)
- `force_inline`: Force inline output regardless of size (default: `false`)
- `force_file`: Force file output regardless of size (default: `false`)

### Parameter Reference Table

| Indicator Type | symbol | interval | time_period | series_type | fastlimit | slowlimit | month (intraday) |
|----------------|--------|----------|-------------|-------------|-----------|-----------|------------------|
| **sma** | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ❌ Rejected | ❌ Rejected | ✅ Optional |
| **ema** | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ❌ Rejected | ❌ Rejected | ✅ Optional |
| **wma** | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ❌ Rejected | ❌ Rejected | ✅ Optional |
| **dema** | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ❌ Rejected | ❌ Rejected | ✅ Optional |
| **tema** | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ❌ Rejected | ❌ Rejected | ✅ Optional |
| **trima** | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ❌ Rejected | ❌ Rejected | ✅ Optional |
| **kama** | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ❌ Rejected | ❌ Rejected | ✅ Optional |
| **t3** | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ❌ Rejected | ❌ Rejected | ✅ Optional |
| **mama** | ✅ Required | ✅ Required | ❌ Rejected | ✅ Required | ✅ Optional (0.01) | ✅ Optional (0.01) | ✅ Optional |
| **vwap** | ✅ Required | ✅ Intraday Only | ❌ Rejected | ❌ Rejected | ❌ Rejected | ❌ Rejected | ✅ Optional |

### Usage Examples

#### 1. Standard Moving Average (SMA)
```python
GET_MOVING_AVERAGE(
    indicator_type="sma",
    symbol="IBM",
    interval="daily",
    time_period=60,
    series_type="close"
)
```

#### 2. Exponential Moving Average (EMA)
```python
GET_MOVING_AVERAGE(
    indicator_type="ema",
    symbol="AAPL",
    interval="weekly",
    time_period=200,
    series_type="high"
)
```

#### 3. MAMA with Custom Limits
```python
GET_MOVING_AVERAGE(
    indicator_type="mama",
    symbol="MSFT",
    interval="daily",
    series_type="close",
    fastlimit=0.02,
    slowlimit=0.05
)
```

#### 4. MAMA with Default Limits
```python
GET_MOVING_AVERAGE(
    indicator_type="mama",
    symbol="GOOGL",
    interval="daily",
    series_type="close"
    # fastlimit and slowlimit default to 0.01
)
```

#### 5. VWAP (Intraday Only)
```python
GET_MOVING_AVERAGE(
    indicator_type="vwap",
    symbol="TSLA",
    interval="5min"
)
```

#### 6. Intraday SMA with Specific Month
```python
GET_MOVING_AVERAGE(
    indicator_type="sma",
    symbol="IBM",
    interval="15min",
    time_period=50,
    series_type="close",
    month="2024-01"
)
```

#### 7. WMA with JSON Output
```python
GET_MOVING_AVERAGE(
    indicator_type="wma",
    symbol="NVDA",
    interval="daily",
    time_period=100,
    series_type="close",
    datatype="json"
)
```

### Migration from Old Tools

If you were using the individual moving average tools, here's how to migrate:

**Old approach:**
```python
SMA(symbol="IBM", interval="daily", time_period=60, series_type="close")
EMA(symbol="AAPL", interval="weekly", time_period=200, series_type="high")
MAMA(symbol="MSFT", interval="daily", series_type="close", fastlimit=0.02, slowlimit=0.05)
VWAP(symbol="TSLA", interval="5min")
```

**New approach:**
```python
GET_MOVING_AVERAGE(indicator_type="sma", symbol="IBM", interval="daily", time_period=60, series_type="close")
GET_MOVING_AVERAGE(indicator_type="ema", symbol="AAPL", interval="weekly", time_period=200, series_type="high")
GET_MOVING_AVERAGE(indicator_type="mama", symbol="MSFT", interval="daily", series_type="close", fastlimit=0.02, slowlimit=0.05)
GET_MOVING_AVERAGE(indicator_type="vwap", symbol="TSLA", interval="5min")
```

**Key Changes:**
- Add `indicator_type` parameter to specify the moving average type
- All other parameters remain the same
- Validation is stricter - invalid parameter combinations will be rejected with clear error messages

### Error Handling

The tool provides clear error messages when parameters don't match the indicator type:

```python
# ❌ Wrong: Missing required time_period for SMA
GET_MOVING_AVERAGE(indicator_type="sma", symbol="IBM", interval="daily", series_type="close")
# Error: "time_period is required for indicator_type='sma'"

# ❌ Wrong: Using time_period with MAMA (uses fastlimit/slowlimit instead)
GET_MOVING_AVERAGE(indicator_type="mama", symbol="IBM", interval="daily", series_type="close", time_period=60)
# Error: "time_period is not valid for indicator_type='mama'. Use fastlimit and slowlimit parameters instead."

# ❌ Wrong: VWAP with non-intraday interval
GET_MOVING_AVERAGE(indicator_type="vwap", symbol="IBM", interval="daily")
# Error: "indicator_type='vwap' only supports intraday intervals. Valid options: 1min, 5min, 15min, 30min, 60min. Got: daily"

# ❌ Wrong: Using series_type with VWAP
GET_MOVING_AVERAGE(indicator_type="vwap", symbol="IBM", interval="5min", series_type="close")
# Error: "series_type is not valid for indicator_type='vwap'. VWAP is calculated from price and volume data automatically."

# ✅ Correct
GET_MOVING_AVERAGE(indicator_type="sma", symbol="IBM", interval="daily", time_period=60, series_type="close")
GET_MOVING_AVERAGE(indicator_type="mama", symbol="IBM", interval="daily", series_type="close", fastlimit=0.02)
GET_MOVING_AVERAGE(indicator_type="vwap", symbol="TSLA", interval="5min")
```

---

### CORE_STOCK_APIS

| Category | Tool | Description |
|----------|------|-------------|
| core_stock_apis | `TIME_SERIES_INTRADAY` | Current and 20+ years of historical intraday OHLCV data |
| core_stock_apis | `TIME_SERIES_DAILY` | Daily time series (OHLCV) covering 20+ years |
| core_stock_apis | `TIME_SERIES_DAILY_ADJUSTED` | Daily adjusted OHLCV with split/dividend events |
| core_stock_apis | `TIME_SERIES_WEEKLY` | Weekly time series (last trading day of week) |
| core_stock_apis | `TIME_SERIES_WEEKLY_ADJUSTED` | Weekly adjusted time series with dividends |
| core_stock_apis | `TIME_SERIES_MONTHLY` | Monthly time series (last trading day of month) |
| core_stock_apis | `TIME_SERIES_MONTHLY_ADJUSTED` | Monthly adjusted time series with dividends |
| core_stock_apis | `GLOBAL_QUOTE` | Latest price and volume for a ticker |
| core_stock_apis | `REALTIME_BULK_QUOTES` | Realtime quotes for up to 100 symbols |
| core_stock_apis | `SYMBOL_SEARCH` | Search for symbols by keywords |
| core_stock_apis | `MARKET_STATUS` | Current market status worldwide |

### OPTIONS_DATA_APIS

| Category | Tool | Description |
|----------|------|-------------|
| options_data_apis | `REALTIME_OPTIONS` | Realtime US options data with Greeks |
| options_data_apis | `HISTORICAL_OPTIONS` | Historical options chain for 15+ years |

### ALPHA_INTELLIGENCE

| Category | Tool | Description |
|----------|------|-------------|
| alpha_intelligence | `NEWS_SENTIMENT` | Live and historical market news & sentiment |
| alpha_intelligence | `EARNINGS_CALL_TRANSCRIPT` | Earnings call transcripts with LLM sentiment |
| alpha_intelligence | `TOP_GAINERS_LOSERS` | Top 20 gainers, losers, and most active |
| alpha_intelligence | `INSIDER_TRANSACTIONS` | Latest and historical insider transactions |
| alpha_intelligence | `ANALYTICS_FIXED_WINDOW` | Advanced analytics over fixed windows |
| alpha_intelligence | `ANALYTICS_SLIDING_WINDOW` | Advanced analytics over sliding windows |

### FUNDAMENTAL_DATA

| Category | Tool | Description |
|----------|------|-------------|
| fundamental_data | `COMPANY_OVERVIEW` | Company information, financial ratios, and metrics |
| fundamental_data | `INCOME_STATEMENT` | Annual and quarterly income statements |
| fundamental_data | `BALANCE_SHEET` | Annual and quarterly balance sheets |
| fundamental_data | `CASH_FLOW` | Annual and quarterly cash flow statements |
| fundamental_data | `EARNINGS` | Annual and quarterly earnings data |
| fundamental_data | `LISTING_STATUS` | Listing and delisting data for equities |
| fundamental_data | `EARNINGS_CALENDAR` | Earnings calendar for upcoming earnings |
| fundamental_data | `IPO_CALENDAR` | Initial public offering calendar |

### FOREX

| Category | Tool | Description |
|----------|------|-------------|
| forex | `FX_INTRADAY` | Intraday foreign exchange rates |
| forex | `FX_DAILY` | Daily foreign exchange rates |
| forex | `FX_WEEKLY` | Weekly foreign exchange rates |
| forex | `FX_MONTHLY` | Monthly foreign exchange rates |

### CRYPTOCURRENCIES

| Category | Tool | Description |
|----------|------|-------------|
| cryptocurrencies | `CURRENCY_EXCHANGE_RATE` | Exchange rate between digital/crypto currencies |
| cryptocurrencies | `DIGITAL_CURRENCY_INTRADAY` | Intraday time series for digital currencies |
| cryptocurrencies | `DIGITAL_CURRENCY_DAILY` | Daily time series for digital currencies |
| cryptocurrencies | `DIGITAL_CURRENCY_WEEKLY` | Weekly time series for digital currencies |
| cryptocurrencies | `DIGITAL_CURRENCY_MONTHLY` | Monthly time series for digital currencies |

### COMMODITIES

| Category | Tool | Description |
|----------|------|-------------|
| commodities | `WTI` | West Texas Intermediate (WTI) crude oil prices |
| commodities | `BRENT` | Brent crude oil prices |
| commodities | `NATURAL_GAS` | Henry Hub natural gas spot prices |
| commodities | `COPPER` | Global copper prices |
| commodities | `ALUMINUM` | Global aluminum prices |
| commodities | `WHEAT` | Global wheat prices |
| commodities | `CORN` | Global corn prices |
| commodities | `COTTON` | Global cotton prices |
| commodities | `SUGAR` | Global sugar prices |
| commodities | `COFFEE` | Global coffee prices |
| commodities | `ALL_COMMODITIES` | All commodities prices |

### ECONOMIC_INDICATORS

| Category | Tool | Description |
|----------|------|-------------|
| economic_indicators | `REAL_GDP` | Real Gross Domestic Product |
| economic_indicators | `REAL_GDP_PER_CAPITA` | Real GDP per capita |
| economic_indicators | `TREASURY_YIELD` | Daily treasury yield rates |
| economic_indicators | `FEDERAL_FUNDS_RATE` | Federal funds rate (interest rates) |
| economic_indicators | `CPI` | Consumer Price Index |
| economic_indicators | `INFLATION` | Inflation rates |
| economic_indicators | `RETAIL_SALES` | Retail sales data |
| economic_indicators | `DURABLES` | Durable goods orders |
| economic_indicators | `UNEMPLOYMENT` | Unemployment rate |
| economic_indicators | `NONFARM_PAYROLL` | Non-farm payroll data |

### TECHNICAL_INDICATORS

| Category | Tool | Description |
|----------|------|-------------|
| technical_indicators | `SMA` | Simple moving average (SMA) values |
| technical_indicators | `EMA` | Exponential moving average (EMA) values |
| technical_indicators | `WMA` | Weighted moving average (WMA) values |
| technical_indicators | `DEMA` | Double exponential moving average (DEMA) values |
| technical_indicators | `TEMA` | Triple exponential moving average (TEMA) values |
| technical_indicators | `TRIMA` | Triangular moving average (TRIMA) values |
| technical_indicators | `KAMA` | Kaufman adaptive moving average (KAMA) values |
| technical_indicators | `MAMA` | MESA adaptive moving average (MAMA) values |
| technical_indicators | `VWAP` | Volume weighted average price (VWAP) for intraday time series |
| technical_indicators | `T3` | Triple exponential moving average (T3) values |
| technical_indicators | `MACD` | Moving average convergence / divergence (MACD) values |
| technical_indicators | `MACDEXT` | Moving average convergence / divergence values with controllable moving average type |
| technical_indicators | `STOCH` | Stochastic oscillator (STOCH) values |
| technical_indicators | `STOCHF` | Stochastic fast (STOCHF) values |
| technical_indicators | `RSI` | Relative strength index (RSI) values |
| technical_indicators | `STOCHRSI` | Stochastic relative strength index (STOCHRSI) values |
| technical_indicators | `WILLR` | Williams' %R (WILLR) values |
| technical_indicators | `ADX` | Average directional movement index (ADX) values |
| technical_indicators | `ADXR` | Average directional movement index rating (ADXR) values |
| technical_indicators | `APO` | Absolute price oscillator (APO) values |
| technical_indicators | `PPO` | Percentage price oscillator (PPO) values |
| technical_indicators | `MOM` | Momentum (MOM) values |
| technical_indicators | `BOP` | Balance of power (BOP) values |
| technical_indicators | `CCI` | Commodity channel index (CCI) values |
| technical_indicators | `CMO` | Chande momentum oscillator (CMO) values |
| technical_indicators | `ROC` | Rate of change (ROC) values |
| technical_indicators | `ROCR` | Rate of change ratio (ROCR) values |
| technical_indicators | `AROON` | Aroon (AROON) values |
| technical_indicators | `AROONOSC` | Aroon oscillator (AROONOSC) values |
| technical_indicators | `MFI` | Money flow index (MFI) values |
| technical_indicators | `TRIX` | 1-day rate of change of a triple smooth exponential moving average (TRIX) values |
| technical_indicators | `ULTOSC` | Ultimate oscillator (ULTOSC) values |
| technical_indicators | `DX` | Directional movement index (DX) values |
| technical_indicators | `MINUS_DI` | Minus directional indicator (MINUS_DI) values |
| technical_indicators | `PLUS_DI` | Plus directional indicator (PLUS_DI) values |
| technical_indicators | `MINUS_DM` | Minus directional movement (MINUS_DM) values |
| technical_indicators | `PLUS_DM` | Plus directional movement (PLUS_DM) values |
| technical_indicators | `BBANDS` | Bollinger bands (BBANDS) values |
| technical_indicators | `MIDPOINT` | Midpoint values - (highest value + lowest value)/2 |
| technical_indicators | `MIDPRICE` | Midpoint price values - (highest high + lowest low)/2 |
| technical_indicators | `SAR` | Parabolic SAR (SAR) values |
| technical_indicators | `TRANGE` | True range (TRANGE) values |
| technical_indicators | `ATR` | Average true range (ATR) values |
| technical_indicators | `NATR` | Normalized average true range (NATR) values |
| technical_indicators | `AD` | Chaikin A/D line (AD) values |
| technical_indicators | `ADOSC` | Chaikin A/D oscillator (ADOSC) values |
| technical_indicators | `OBV` | On balance volume (OBV) values |
| technical_indicators | `HT_TRENDLINE` | Hilbert transform, instantaneous trendline (HT_TRENDLINE) values |
| technical_indicators | `HT_SINE` | Hilbert transform, sine wave (HT_SINE) values |
| technical_indicators | `HT_TRENDMODE` | Hilbert transform, trend vs cycle mode (HT_TRENDMODE) values |
| technical_indicators | `HT_DCPERIOD` | Hilbert transform, dominant cycle period (HT_DCPERIOD) values |
| technical_indicators | `HT_DCPHASE` | Hilbert transform, dominant cycle phase (HT_DCPHASE) values |
| technical_indicators | `HT_PHASOR` | Hilbert transform, phasor components (HT_PHASOR) values |

### PING

| Category | Tool | Description |
|----------|------|-------------|
| ping | `PING` | Health check tool that returns 'pong' |
| ping | `ADD_TWO_NUMBERS` | Example tool for adding two numbers |
