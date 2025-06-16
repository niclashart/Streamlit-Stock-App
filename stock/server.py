import yfinance as yf
import pandas as pd
from flask import Flask, jsonify, request
import json

app = Flask(__name__)


@app.route("/info/<ticker>", methods=["GET"])
def get_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if (
            not info or info.get("trailingPegRatio") is None
        ):  # Check for empty or minimal info
            # Attempt to get at least the name and current price if full info is missing
            hist = stock.history(period="2d")
            if not hist.empty:
                current_price = (
                    f"${hist['Close'].iloc[-1]:.2f}"
                    if not hist["Close"].empty
                    else "N/A"
                )
                # Try to get company name from shortName or longName if available
                name = info.get("shortName", info.get("longName", ticker))
                return jsonify(
                    {
                        "name": name,
                        "current_price": current_price,
                        "warning": "Limited data available for this ticker.",
                    }
                )
            return (
                jsonify(
                    {
                        "error": f"Could not retrieve valid stock information for {ticker}. It might be delisted or an incorrect symbol."
                    }
                ),
                404,
            )

        # Format data similar to the original get_yfinance_stock_info
        formatted_info = {
            "name": info.get("shortName", info.get("longName", ticker)),
            "current_price": f"${info.get('currentPrice', info.get('previousClose', 0.0)):.2f}",
            "market_cap": f"${info.get('marketCap', 0):,}",
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "dividend_rate": info.get("dividendRate", "N/A"),
            "beta": info.get("beta", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "eps": info.get("trailingEps", "N/A"),
            "volume": f"{info.get('volume', 0):,}",
            "day_high": f"${info.get('dayHigh', 0.0):.2f}",
            "day_low": f"${info.get('dayLow', 0.0):.2f}",
            "fifty_two_week_high": f"${info.get('fiftyTwoWeekHigh', 0.0):.2f}",
            "fifty_two_week_low": f"${info.get('fiftyTwoWeekLow', 0.0):.2f}",
        }
        return jsonify(formatted_info)
    except Exception as e:
        print(f"Error in get_info for {ticker}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/history", methods=["GET"])
def get_history():
    tickers_str = request.args.get("tickers")  # Comma-separated string
    start_date = request.args.get("start", "2015-01-01")
    if not tickers_str:
        return jsonify({"error": "'tickers' query parameter is required"}), 400

    tickers = tickers_str.split(",")
    data = pd.DataFrame()
    warnings = []
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(start=start_date)
            if "Close" in hist.columns:
                data[ticker] = hist["Close"]
            else:
                warnings.append(f"No 'Close' data for {ticker}")
        except Exception as e:
            warnings.append(f"Could not load {ticker}: {e}")
            print(f"Error loading history for {ticker}: {e}")

    response_data = json.loads(data.to_json(orient="split", date_format="iso"))
    if warnings:
        response_data["warnings"] = warnings
    return jsonify(response_data)


@app.route("/dividends/<ticker>", methods=["GET"])
def get_divs(ticker):
    try:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends  # pd.Series

        if dividends.empty:
            # Return structure consistent with successful empty response
            return jsonify(json.loads(pd.Series(dtype="float64").to_json(orient="split", date_format="iso")))

        # Filter dividends
        comparison_date_naive = pd.to_datetime("2015-01-01")

        # Ensure comparison_date is compatible with dividends.index timezone
        if dividends.index.tz is not None:
            # If dividends.index is timezone-aware, make comparison_date aware of the same timezone
            comparison_date = comparison_date_naive.tz_localize(dividends.index.tz)
        else:
            # If dividends.index is naive, comparison_date remains naive
            comparison_date = comparison_date_naive

        dividends_filtered = dividends[dividends.index > comparison_date]

        # Convert to a format suitable for JSON, client expects "split"
        dividends_json_payload = json.loads(
            dividends_filtered.to_json(orient="split", date_format="iso")
        )
        return jsonify(dividends_json_payload)
    except Exception as e:
        print(f"Error in get_dividends for {ticker}: {e}")
        # Return an empty Series representation in case of an error, maintaining a 200 OK status
        # as the client side (app.py) is designed to handle empty data gracefully.
        empty_dividends_payload = json.loads(pd.Series(dtype="float64").to_json(orient="split", date_format="iso"))
        return jsonify(empty_dividends_payload)  # Default 200 OK


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
