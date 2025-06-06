import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

from src.services.stock_service import StockService

def stock_analysis_view(ticker=None):
    """Individual stock analysis view"""
    if not ticker:
        ticker = st.text_input("📊 Gib ein Ticker-Symbol ein", max_chars=10).upper()
        if not ticker:
            st.info("Bitte gib ein Ticker-Symbol ein, um eine Analyse zu sehen.")
            return
        st.session_state["selected_ticker"] = ticker

    st.title(f"📄 Analyse: {ticker}")
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="6mo")
        
        if hist.empty:
            st.error(f"Keine Daten für {ticker} gefunden. Bitte überprüfe das Ticker-Symbol.")
            return
            
        # Display key metrics
        col1, col2 = st.columns(2)
        col1.metric("Aktueller Kurs", f"${hist['Close'].iloc[-1]:.2f}")
        col2.metric("Tagesveränderung", f"${hist['Close'].iloc[-1] - hist['Open'].iloc[-1]:.2f}")

        col3, col4 = st.columns(2)
        col3.metric("Marktkapitalisierung", f"${info.get('marketCap', 0):,}")
        col4.metric("Dividende/Aktie", f"${info.get('dividendRate', 0):.2f}")

        # Display price chart
        st.subheader("📈 Kursverlauf (6 Monate)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], name="Close"))
        fig.update_layout(xaxis_title="Datum", yaxis_title="Preis ($)")
        st.plotly_chart(fig, use_container_width=True)
        
        # Company information
        st.subheader("🏢 Unternehmensinformationen")
        col1, col2 = st.columns(2)
        
        col1.write(f"**Name:** {info.get('shortName', 'N/A')}")
        col1.write(f"**Sektor:** {info.get('sector', 'N/A')}")
        col1.write(f"**Industrie:** {info.get('industry', 'N/A')}")
        
        col2.write(f"**KGV:** {info.get('trailingPE', 'N/A')}")
        col2.write(f"**EPS:** {info.get('trailingEps', 'N/A')}")
        col2.write(f"**Dividendenrendite:** {info.get('dividendYield', 0) * 100:.2f}%")
        
        # Recent news
        st.subheader("📰 Aktuelle Nachrichten")
        news = stock.news[:5] if hasattr(stock, 'news') else []
        
        if news:
            for item in news:
                st.write(f"**{item['title']}**")
                st.write(f"*{item['publisher']}*")
                st.write(item['link'])
                st.write("---")
        else:
            st.info("Keine aktuellen Nachrichten verfügbar.")
            
    except Exception as e:
        st.error(f"Fehler beim Laden der Daten für {ticker}: {str(e)}")
        return
