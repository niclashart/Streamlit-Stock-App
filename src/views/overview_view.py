import streamlit as st
import pandas as pd
from datetime import datetime
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from src.models.portfolio import PortfolioModel
from src.services.stock_service import StockService

def overview_view(username):
    """Portfolio overview view"""
    st.title("📈 Portfolio Übersicht")
    df = PortfolioModel.load(username)
    
    if df.empty:
        st.info("Dein Portfolio ist leer. Füge Aktien hinzu, um deine Übersicht zu sehen.")
        return

    # Get all tickers from portfolio
    tickers = df["Ticker"].tolist()
    
    # Add benchmarks
    benchmarks = {
        "S&P 500": "^GSPC",
        "Nasdaq": "^IXIC",
        "MSCI World": "URTH"
    }
    selected_benchmarks = st.multiselect(
        "🔍 Benchmarks auswählen", 
        options=list(benchmarks.keys()), 
        default=["S&P 500"]
    )
    all_tickers = tickers + [benchmarks[b] for b in selected_benchmarks]

    # Get price history
    data = StockService.get_price_history(all_tickers)
    
    if data.empty:
        st.error("Keine Daten gefunden. Überprüfe deine Ticker-Symbole.")
        return

    # Calculate portfolio metrics
    latest_prices = data.iloc[-1]
    df["Aktueller Kurs"] = df["Ticker"].map(latest_prices)
    df["Kaufwert"] = df["Anteile"] * df["Einstiegspreis"]
    df["Aktueller Wert"] = df["Anteile"] * df["Aktueller Kurs"]
    df["Gewinn/Verlust €"] = df["Aktueller Wert"] - df["Kaufwert"]
    df["Gewinn/Verlust %"] = (df["Gewinn/Verlust €"] / df["Kaufwert"]) * 100

    total_value = df["Aktueller Wert"].sum()
    total_cost = df["Kaufwert"].sum()

    # Display summary metrics
    col1, col2 = st.columns(2)
    col1.metric("📦 Gesamtwert", f"${total_value:,.2f}")
    col2.metric(
        "📈 Performance", 
        f"{((total_value - total_cost)/total_cost)*100:.2f}%", 
        delta=f"${(total_value - total_cost):,.2f}"
    )

    # Portfolio history chart
    st.subheader("📊 Portfolio Verlauf")

    shares_dict = dict(zip(df["Ticker"], df["Anteile"]))
    portfolio_history = pd.DataFrame(index=data.index)

    # Calculate portfolio value over time considering purchase date
    for ticker, row in df.iterrows():
        ticker_symbol = row["Ticker"]
        purchase_date = row["Kaufdatum"]
        
        if ticker_symbol in data.columns:
            ticker_data = data[ticker_symbol].copy()
            # Zero out values before purchase date
            ticker_data.loc[ticker_data.index < purchase_date] = 0
            portfolio_history[ticker_symbol] = ticker_data * row["Anteile"]

    # Total portfolio value over time
    portfolio_history["Total"] = portfolio_history.sum(axis=1)

    # Determine initial invested value
    valid_values = portfolio_history["Total"][portfolio_history["Total"] > 0]
    if not valid_values.empty:
        first_date = valid_values.index[0]
        initial_value = valid_values.iloc[0]
    else:
        first_date = data.index[0]
        initial_value = 0

    # Create plot
    fig = make_subplots()
    fig.add_trace(go.Scatter(
        x=portfolio_history.index,
        y=portfolio_history["Total"],
        name="Portfolio",
        line=dict(width=3)
    ))

    # Add normalized benchmarks
    for name in selected_benchmarks:
        ticker = benchmarks[name]
        if ticker in data.columns:
            benchmark_data = data[ticker].copy()
            
            # Normalize to same starting point as portfolio
            if not benchmark_data.empty and initial_value > 0:
                benchmark_value_at_start = benchmark_data.loc[benchmark_data.index >= first_date].iloc[0]
                normalization_factor = initial_value / benchmark_value_at_start
                normalized_benchmark = benchmark_data * normalization_factor
                
                fig.add_trace(go.Scatter(
                    x=normalized_benchmark.index,
                    y=normalized_benchmark,
                    name=name,
                    line=dict(dash='dash')
                ))

    # Update layout
    fig.update_layout(
        title="Wertentwicklung",
        xaxis_title="Datum",
        yaxis_title="Wert in $",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    # Portfolio details
    st.subheader("🧾 Portfolio Details")
    st.dataframe(df.set_index("Ticker").round(2), use_container_width=True)

    # Dividends
    st.subheader("💸 Dividenden")
    dividend_data = []
    for ticker in tickers:
        divs = StockService.get_dividends(ticker)
        if not divs.empty:
            annual_total = divs.resample('Y').sum()
            shares = df.loc[df["Ticker"] == ticker, "Anteile"].values[0]
            
            for year, amount in annual_total.items():
                dividend_data.append({
                    "Ticker": ticker,
                    "Jahr": year.year,
                    "Dividende/Aktie": amount,
                    "Anteile": shares,
                    "Ertrag": amount * shares
                })

    if dividend_data:
        dividend_df = pd.DataFrame(dividend_data)
        st.dataframe(dividend_df, use_container_width=True)
    else:
        st.info("Keine Dividendendaten verfügbar.")

    # Rebalancing analysis
    st.subheader("⚖️ Rebalancing Analyse")
    df["Gewichtung"] = df["Aktueller Wert"] / total_value * 100
    target = 100 / len(df)
    df["Abweichung"] = df["Gewichtung"] - target
    st.dataframe(df[["Ticker", "Aktueller Wert", "Gewichtung", "Abweichung"]].set_index("Ticker").round(2))
