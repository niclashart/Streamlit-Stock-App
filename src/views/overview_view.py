"""
Overview view for displaying portfolio performance and metrics
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
import pandas as pd
from models.portfolio import PortfolioService
from models.order import OrderService, Order
from services.stock_service import StockService
from utils.chart_utils import (
    calculate_portfolio_metrics,
    create_portfolio_chart,
    create_portfolio_allocation_chart,
    format_currency,
    format_percentage
)

def show_overview_view() -> None:
    """Display the portfolio overview view"""
    st.title("📈 Portfolio Übersicht")
    
    # Initialize portfolio service
    portfolio_service = PortfolioService(st.session_state["username"])
    portfolio = portfolio_service.load_portfolio()
    
    # Initialize order service to get pending orders
    order_service = OrderService()
    pending_orders = order_service.get_pending_orders(st.session_state["username"])
    
    # Display pending orders section at the top
    if pending_orders:
        st.subheader("⏳ Deine ausstehenden Orders")
        
        # Create a DataFrame for pending orders
        order_data = []
        for order in pending_orders:
            # Get current price for comparison
            current_price = StockService.get_current_price(order.ticker)
            
            # Calculate price difference
            price_diff = ""
            if current_price:
                if order.order_type == "buy":
                    diff = order.price - current_price
                    diff_percent = (diff / current_price) * 100
                    status = "🟢 Ausführbar" if current_price <= order.price else f"🟠 {abs(diff_percent):.1f}% entfernt"
                else:  # sell order
                    diff = current_price - order.price
                    diff_percent = (diff / order.price) * 100
                    status = "🟢 Ausführbar" if current_price >= order.price else f"🟠 {abs(diff_percent):.1f}% entfernt"
            else:
                status = "⚪ Unbekannt"
            
            order_data.append({
                "Ticker": order.ticker,
                "Typ": order.order_type.upper(),
                "Zielpreis": f"${order.price:.2f}",
                "Anzahl": order.quantity,
                "Aktueller Preis": f"${current_price:.2f}" if current_price else "Nicht verfügbar",
                "Status": status
            })
        
        # Display as a DataFrame
        if order_data:
            order_df = pd.DataFrame(order_data)
            st.dataframe(order_df.set_index("Ticker"), use_container_width=True)
            
            # Add note about order execution
            st.info("ℹ️ Orders werden automatisch ausgeführt, wenn der Zielpreis erreicht ist. Prüfung alle 30 Sekunden.")
        
        # Add visual separator
        st.markdown("---")
    
    if not portfolio.positions:
        st.warning("Bitte erfasse zuerst Positionen unter 'Portfolio verwalten'.")
        st.stop()

    # Get tickers from portfolio
    tickers = [p.ticker for p in portfolio.positions]
    
    # Select benchmarks
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
    
    # Get all tickers (portfolio + benchmarks)
    all_tickers = tickers + [benchmarks[b] for b in selected_benchmarks]

    # Get price history
    with st.spinner("Lade Kursdaten..."):
        data = StockService.get_price_history(all_tickers)
    
    if data.empty:
        st.warning("⚠️ Keine Kursdaten gefunden.")
        st.stop()

    # Get latest prices and update portfolio
    latest_prices = data.iloc[-1]
    
    # Update portfolio with current prices
    df = portfolio.to_dataframe()
    df["Aktueller Kurs"] = df["Ticker"].map(latest_prices)
    df["Kaufwert"] = df["Anteile"] * df["Einstiegspreis"]
    df["Aktueller Wert"] = df["Anteile"] * df["Aktueller Kurs"]
    df["Gewinn/Verlust €"] = df["Aktueller Wert"] - df["Kaufwert"]
    df["Gewinn/Verlust %"] = (df["Gewinn/Verlust €"] / df["Kaufwert"]) * 100

    # Calculate portfolio metrics
    metrics = calculate_portfolio_metrics(df)

    # Display metrics
    col1, col2 = st.columns(2)
    col1.metric("📦 Gesamtwert", format_currency(metrics["total_value"]))
    col2.metric(
        "📈 Performance", 
        format_percentage(metrics["total_profit_loss_percent"]), 
        delta=format_currency(metrics["total_profit_loss"])
    )

    # Create portfolio history dataframe
    shares_dict = dict(zip(df["Ticker"], df["Anteile"]))
    portfolio_history = pd.DataFrame(index=data.index)

    # Calculate portfolio values considering purchase date
    for _, row in df.iterrows():
        ticker = row["Ticker"]
        anzahl = row["Anteile"]
        kaufdatum = row["Kaufdatum"]

        if ticker in data.columns:
            werte = data[ticker].copy()
            werte[data.index.tz_localize(None) < pd.to_datetime(kaufdatum)] = 0  # Mask before purchase date
            portfolio_history[ticker] = werte * anzahl

    # Total portfolio value over time
    portfolio_history["Total"] = portfolio_history.sum(axis=1)
    
    # Create benchmark dictionary
    benchmark_data = {}
    for name in selected_benchmarks:
        bm_symbol = benchmarks[name]
        if bm_symbol in data.columns:
            benchmark_data[name] = data[bm_symbol]

    # Create and display portfolio chart
    st.subheader("📊 Portfolio Verlauf")
    fig = create_portfolio_chart(portfolio_history, benchmark_data)
    st.plotly_chart(fig, use_container_width=True)
    
    # Display portfolio allocation chart
    st.subheader("⚖️ Portfolio Verteilung")
    pie_fig = create_portfolio_allocation_chart(df)
    st.plotly_chart(pie_fig, use_container_width=True)

    # Portfolio details
    st.subheader("🧾 Portfolio Details")
    for i, position in enumerate(portfolio.positions):
        ticker = position.ticker
        if st.button(f"{ticker} auswählen", key=f"select_{i}"):
            st.session_state["selected_ticker"] = ticker
            st.rerun()
    
    # Display dataframe
    st.dataframe(df.set_index("Ticker").round(2), use_container_width=True)

    # Dividends
    st.subheader("💸 Dividenden")
    dividend_data = []
    for ticker in tickers:
        divs = StockService.get_dividends(ticker)
        if not divs.empty:
            row = df[df["Ticker"] == ticker].iloc[0]
            total = divs.sum() * row["Anteile"]
            dividend_data.append((ticker, total, len(divs)))
            
    if dividend_data:
        div_df = pd.DataFrame(dividend_data, columns=["Ticker", "Summe Dividenden ($)", "Zahlungen"])
        st.dataframe(div_df.set_index("Ticker").round(2))
    else:
        st.info("Keine Dividenden im aktuellen Zeitraum.")

    # Rebalancing analysis
    st.subheader("⚖️ Rebalancing Analyse")
    df["Gewichtung"] = df["Aktueller Wert"] / metrics["total_value"] * 100
    target = 100 / len(df)
    df["Abweichung"] = df["Gewichtung"] - target
    st.dataframe(df[["Ticker", "Aktueller Wert", "Gewichtung", "Abweichung"]].set_index("Ticker").round(2))
