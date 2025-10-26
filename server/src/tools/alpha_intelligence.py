from src.common import _make_api_request
from src.tools.registry import tool


@tool
def news_sentiment(
    tickers: str = None,
    topics: str = None,
    time_from: str = None,
    time_to: str = None,
    sort: str = "LATEST",
    limit: int = 10,
    output: str = "auto",
    project: str = None,
    category: str = None,
    filename: str = None,
) -> dict[str, str] | str:
    """Returns live and historical market news & sentiment data from premier news outlets worldwide.

    Covers stocks, cryptocurrencies, forex, and topics like fiscal policy, mergers & acquisitions, IPOs.

    ⚠️ WARNING: Each news article can be quite large. Default limit is 10 to prevent token overflow.
    Use smaller limits (1-5) for initial queries, then increase if needed.

    Args:
        tickers: Stock/crypto/forex symbols to filter articles. Example: "IBM" or "COIN,CRYPTO:BTC,FOREX:USD".
        topics: News topics to filter by. Example: "technology" or "technology,ipo".
        time_from: Start time range in YYYYMMDDTHHMM format. Example: "20220410T0130".
        time_to: End time range in YYYYMMDDTHHMM format. Defaults to current time if time_from specified.
        sort: Sort order - "LATEST" (default), "EARLIEST", or "RELEVANCE".
        limit: Number of results to return. Default 10 (reduced from 50 to prevent token overflow). Max 1000.
        output: Output mode for response handling:
               - "auto": Automatically decide based on response size (default)
               - "screen": Force return in response (may be truncated if large)
               - "file": Always save to file (requires project parameter)
        project: Project name for saving data. Creates project if it doesn't exist.
        category: Optional category subdirectory within project.
        filename: Optional custom filename. Auto-generated if not specified.

    Returns:
        Dictionary containing news sentiment data, or file metadata if saved to disk.
    """

    params = {
        "sort": sort,
        "limit": str(limit),
    }
    if tickers:
        params["tickers"] = tickers
    if topics:
        params["topics"] = topics
    if time_from:
        params["time_from"] = time_from
    if time_to:
        params["time_to"] = time_to

    return _make_api_request(
        "NEWS_SENTIMENT",
        params,
        output=output,
        project=project,
        category=category,
        filename=filename,
    )


@tool
def earnings_call_transcript(symbol: str, quarter: str) -> dict[str, str] | str:
    """Returns earnings call transcript for a company in a specific quarter.

    Covers 15+ years of history enriched with LLM-based sentiment signals.

    Args:
        symbol: Ticker symbol. Example: "IBM".
        quarter: Fiscal quarter in YYYYQM format. Example: "2024Q1". Supports quarters since 2010Q1.

    Returns:
        Dictionary containing earnings call transcript data or JSON string.
    """

    params = {
        "symbol": symbol,
        "quarter": quarter,
    }

    return _make_api_request("EARNINGS_CALL_TRANSCRIPT", params, output=output, project=project, category=category, filename=filename)


@tool
def top_gainers_losers() -> dict[str, str] | str:
    """Returns top 20 gainers, losers, and most active traded tickers in the US market.

    Args:
        None.

    Returns:
        Dictionary containing top gainers/losers data or JSON string.
    """

    params = {}

    return _make_api_request("TOP_GAINERS_LOSERS", params, output=output, project=project, category=category, filename=filename)


@tool
def insider_transactions(symbol: str) -> dict[str, str] | str:
    """Returns latest and historical insider transactions by key stakeholders.

    Covers transactions by founders, executives, board members, etc.

    Args:
        symbol: Ticker symbol. Example: "IBM".

    Returns:
        Dictionary containing insider transaction data or JSON string.
    """

    params = {
        "symbol": symbol,
    }

    return _make_api_request("INSIDER_TRANSACTIONS", params, output=output, project=project, category=category, filename=filename)


@tool
def analytics_fixed_window(
    symbols: str, range_param: str, interval: str, calculations: str, ohlc: str = "close"
) -> dict[str, str] | str:
    """Returns advanced analytics metrics for time series over a fixed temporal window.

    Calculates metrics like total return, variance, auto-correlation, etc.

    Args:
        symbols: Comma-separated list of symbols. Free keys: up to 5, Premium keys: up to 50.
        range_param: Date range for the series. Defaults to full equity history.
        interval: Time interval - 1min, 5min, 15min, 30min, 60min, DAILY, WEEKLY, MONTHLY.
        calculations: Comma-separated list of analytics metrics to calculate.
        ohlc: OHLC field for calculation - open, high, low, close. Default "close".

    Returns:
        Dictionary containing analytics data or JSON string.
    """

    params = {
        "SYMBOLS": symbols,
        "RANGE": range_param,
        "INTERVAL": interval,
        "CALCULATIONS": calculations,
        "OHLC": ohlc,
    }

    return _make_api_request("ANALYTICS_FIXED_WINDOW", params, output=output, project=project, category=category, filename=filename)


@tool
def analytics_sliding_window(
    symbols: str,
    range_param: str,
    interval: str,
    window_size: int,
    calculations: str,
    ohlc: str = "close",
) -> dict[str, str] | str:
    """Returns advanced analytics metrics for time series over sliding time windows.

    Calculates moving metrics like variance over time periods. Example: moving variance over 5 years with 100-point window.

    Args:
        symbols: Comma-separated list of symbols. Free keys: up to 5, Premium keys: up to 50.
        range_param: Date range for the series. Defaults to full equity history.
        interval: Time interval - 1min, 5min, 15min, 30min, 60min, DAILY, WEEKLY, MONTHLY.
        window_size: Size of moving window. Minimum 10, larger recommended for statistical significance.
        calculations: Comma-separated analytics metrics. Free keys: 1 metric, Premium keys: multiple.
        ohlc: OHLC field for calculation - open, high, low, close. Default "close".

    Returns:
        Dictionary containing sliding window analytics data or JSON string.
    """

    params = {
        "SYMBOLS": symbols,
        "RANGE": range_param,
        "INTERVAL": interval,
        "WINDOW_SIZE": str(window_size),
        "CALCULATIONS": calculations,
        "OHLC": ohlc,
    }

    return _make_api_request("ANALYTICS_SLIDING_WINDOW", params, output=output, project=project, category=category, filename=filename)
