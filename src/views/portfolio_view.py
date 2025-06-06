import streamlit as st
import pandas as pd
from datetime import datetime

from src.models.portfolio import PortfolioModel

def portfolio_management_view(username):
    """Portfolio management view"""
    st.title("📋 Portfolio verwalten")
    
    # Load current portfolio
    df = PortfolioModel.load(username)
    
    # Add stock form
    with st.form("portfolio_form"):
        st.subheader("📝 Aktie hinzufügen")
        
        col1, col2 = st.columns(2)
        ticker = col1.text_input("Ticker Symbol", max_chars=10).upper()
        shares = col2.number_input("Anzahl der Anteile", min_value=0.01, step=0.01)
        
        col3, col4 = st.columns(2)
        price = col3.number_input("Einstiegspreis ($)", min_value=0.01, step=0.01)
        purchase_date = col4.date_input("Kaufdatum")
        
        submit = st.form_submit_button("Hinzufügen")
        
        if submit and ticker and shares > 0 and price > 0:
            # Create new entry
            new_entry = pd.DataFrame([{
                "Ticker": ticker,
                "Anteile": shares,
                "Einstiegspreis": price,
                "Kaufdatum": datetime.combine(purchase_date, datetime.min.time())
            }])
            
            # Check if ticker already exists
            if ticker in df["Ticker"].values:
                # Update existing entry
                df.loc[df["Ticker"] == ticker, "Anteile"] = shares
                df.loc[df["Ticker"] == ticker, "Einstiegspreis"] = price
                df.loc[df["Ticker"] == ticker, "Kaufdatum"] = datetime.combine(purchase_date, datetime.min.time())
                st.success(f"Aktie {ticker} aktualisiert!")
            else:
                # Append new entry
                df = pd.concat([df, new_entry], ignore_index=True)
                st.success(f"Aktie {ticker} hinzugefügt!")
            
            # Save portfolio
            PortfolioModel.save(username, df)
            
            # Clear form (doesn't work in Streamlit yet, but keeping for future)
            ticker = ""
            shares = 0.01
            price = 0.01
    
    # Display current portfolio
    st.subheader("📦 Aktuelles Portfolio")
    
    if df.empty:
        st.info("Dein Portfolio ist leer. Füge Aktien hinzu, um sie hier zu sehen.")
    else:
        # Add delete button for each row
        for i, row in df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
            col1.write(row["Ticker"])
            col2.write(f"{row['Anteile']}")
            col3.write(f"${row['Einstiegspreis']:.2f}")
            col4.write(row["Kaufdatum"].strftime("%Y-%m-%d"))
            
            if col5.button("🗑️", key=f"delete_{i}"):
                df = df.drop(i).reset_index(drop=True)
                PortfolioModel.save(username, df)
                st.success(f"Aktie {row['Ticker']} entfernt!")
                st.rerun()
        
        st.dataframe(df.set_index("Ticker"), use_container_width=True)
