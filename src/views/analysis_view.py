"""
Stock analysis view for displaying detailed analysis of a single stock
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
import yfinance as yf
from services.stock_service import StockService
from utils.chart_utils import create_stock_chart

def show_analysis_view() -> None:
    """Display the stock analysis view"""
    ticker = st.session_state.get("selected_ticker")
    if not ticker:
        st.info("Bitte wähle eine Aktie in der Übersicht.")
        st.stop()

    st.title(f"📄 Analyse: {ticker}")
    
    # Get stock data
    with st.spinner(f"Lade Daten für {ticker}..."):
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="6mo")

    if hist.empty:
        st.error(f"Keine Daten für {ticker} gefunden.")
        st.stop()

    # Display basic metrics
    col1, col2 = st.columns(2)
    col1.metric("Aktueller Kurs", f"${hist['Close'].iloc[-1]:.2f}")
    col2.metric("Tagesveränderung", f"${hist['Close'].iloc[-1] - hist['Open'].iloc[-1]:.2f}")

    col3, col4 = st.columns(2)
    col3.metric("Marktkapitalisierung", f"${info.get('marketCap', 0):,}")
    col4.metric("Dividende/Aktie", f"${info.get('dividendRate', 0):.2f}")

    # Display price chart
    st.subheader("📈 Kursverlauf (6 Monate)")
    fig = create_stock_chart(hist, title=f"{ticker} - Kursverlauf")
    st.plotly_chart(fig, use_container_width=True)
    
    # Company info
    st.subheader("🏢 Unternehmensinformationen")
    company_info = {
        "Name": info.get("longName", "N/A"),
        "Branche": info.get("industry", "N/A"),
        "Sektor": info.get("sector", "N/A"),
        "Website": info.get("website", "N/A"),
        "Beschreibung": info.get("longBusinessSummary", "N/A")
    }
    
    for key, value in company_info.items():
        if key == "Beschreibung":
            st.write(f"**{key}**:")
            st.write(value)
        elif key == "Website" and value != "N/A":
            st.write(f"**{key}**: [{value}]({value})")
        else:
            st.write(f"**{key}**: {value}")
            
    # Financial metrics
    st.subheader("📊 Finanzkennzahlen")
    metrics = {
        "P/E Ratio": info.get("trailingPE", "N/A"),
        "EPS (TTM)": info.get("trailingEps", "N/A"),
        "Gewinnmarge": info.get("profitMargins", "N/A"),
        "ROE": info.get("returnOnEquity", "N/A"),
        "Beta": info.get("beta", "N/A"),
        "52-Wochen Tief": info.get("fiftyTwoWeekLow", "N/A"),
        "52-Wochen Hoch": info.get("fiftyTwoWeekHigh", "N/A"),
        "Durchschn. Volumen": info.get("averageVolume", "N/A"),
        "Div. Rendite": info.get("dividendYield", "N/A")
    }
    
    col1, col2 = st.columns(2)
    
    # Format and display the metrics in two columns
    metrics_items = list(metrics.items())
    half = len(metrics_items) // 2 + len(metrics_items) % 2
    
    for i, (key, value) in enumerate(metrics_items):
        if i < half:
            column = col1
        else:
            column = col2
            
        if key == "Div. Rendite" and value != "N/A":
            column.metric(key, f"{value * 100:.2f}%")
        elif isinstance(value, (int, float)) and key not in ["P/E Ratio", "EPS (TTM)", "Beta"]:
            column.metric(key, f"{value:,}")
        elif isinstance(value, (int, float)):
            column.metric(key, f"{value:.2f}")
        else:
            column.metric(key, value)
            
    # News section
    st.subheader("📰 Aktuelle Nachrichten")
    news = stock.news[:5] if hasattr(stock, 'news') and stock.news else []
    
    if news:
        for item in news:
            st.write(f"**{item.get('title')}**")
            st.write(f"*{item.get('publisher')}* - {item.get('providerPublishTime')}")
            st.write(f"[Artikel lesen]({item.get('link')})")
            st.write("---")
    else:
        st.info("Keine aktuellen Nachrichten verfügbar.")
