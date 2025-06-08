"""
Portfolio management view for adding, editing, and removing portfolio positions
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from datetime import date
import pandas as pd
from models.portfolio import PortfolioService, Position
from services.stock_service import StockService

def show_portfolio_management_view() -> None:
    """Display the portfolio management view"""
    st.title("📋 Portfolio verwalten")
    
    # Initialize portfolio service
    portfolio_service = PortfolioService(st.session_state["username"])
    portfolio = portfolio_service.load_portfolio()
    
    # Form to add new position
    with st.form("portfolio_form"):
        st.subheader("Neue Position hinzufügen")
        ticker = st.text_input("Ticker (z. B. AAPL)").upper()
        anteile = st.number_input("Anzahl der Anteile", min_value=0.0, value=0.0)
        preis = st.number_input("Einstiegspreis ($)", min_value=0.0, value=0.0)
        kaufdatum = st.date_input("Kaufdatum", value=date.today())
        submitted = st.form_submit_button("Hinzufügen")

        if submitted and ticker:
            # Validate ticker
            if StockService.validate_ticker(ticker):
                portfolio_service.add_position(
                    ticker=ticker,
                    shares=anteile,
                    entry_price=preis,
                    purchase_date=kaufdatum
                )
                st.success(f"{ticker} hinzugefügt!")
                st.rerun()
            else:
                st.error(f"Ticker '{ticker}' konnte nicht validiert werden. Bitte überprüfe das Symbol.")

    # Display current portfolio
    st.subheader("📦 Aktuelles Portfolio")
    df = portfolio.to_dataframe()
    
    if not df.empty:
        # Add action column with delete buttons
        for i, row in df.reset_index().iterrows():
            col1, col2 = st.columns([4, 1])
            col1.write(f"{row['Ticker']} - {row['Anteile']} Anteile @ ${row['Einstiegspreis']:.2f}")
            if col2.button("🗑️", key=f"delete_{i}"):
                if portfolio_service.remove_position(row['Ticker']):
                    st.success(f"{row['Ticker']} wurde aus dem Portfolio entfernt.")
                    st.rerun()
        
        # Display detailed portfolio table
        st.dataframe(df.set_index("Ticker"), use_container_width=True)
    else:
        st.info("Dein Portfolio ist aktuell leer. Füge neue Positionen hinzu.")
