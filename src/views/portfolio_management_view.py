"""
Portfolio management view for adding, editing, and removing portfolio positions
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from datetime import date, datetime, timedelta
import pandas as pd
from models.portfolio import PortfolioService, Position
from services.stock_service import StockService
import yfinance as yf

def show_portfolio_management_view() -> None:
    """Display the portfolio management view"""
    st.title("📋 Portfolio verwalten")
    
    # Initialize portfolio service
    portfolio_service = PortfolioService(st.session_state["username"])
    portfolio = portfolio_service.load_portfolio()
    
    # Create tabs for different portfolio operations
    tab1, tab2 = st.tabs(["🛒 Neue Order erstellen", "📝 Historische Position hinzufügen"])
    
    # Tab 1: Create new order
    with tab1:
        st.warning("⚠️ Neue Orders werden als Pending-Orders erstellt und erst ausgeführt, wenn der aktuelle Marktpreis deinen angegebenen Zielpreis erreicht hat.")
        
        # Form to create new buy order
        with st.form("order_form"):
            st.subheader("Neue Kauf-Order erstellen")
            ticker = st.text_input("Ticker (z. B. AAPL)", key="order_ticker").upper()
            anteile = st.number_input("Anzahl der Anteile", min_value=0.0, value=1.0, key="order_shares")
            
            # Try to get current price if ticker is entered
            current_price = None
            if ticker:
                try:
                    current_price = StockService.get_current_price(ticker)
                    if current_price:
                        st.metric("Aktueller Preis", f"${current_price:.2f}")
                except:
                    pass
                    
            # Default is 5% below current price if available
            default_price = round(current_price * 0.95, 2) if current_price else 0.0
            preis = st.number_input("Zielpreis für Kauf ($)", min_value=0.0, value=default_price, 
                                  help="Die Order wird ausgeführt, wenn der aktuelle Preis unter oder gleich diesem Wert ist",
                                  key="order_price")
            submitted = st.form_submit_button("Order erstellen")

            if submitted and ticker and anteile > 0:
                # Validate ticker
                if StockService.validate_ticker(ticker):
                    # Create a pending buy order instead of directly adding to portfolio
                    from src.models.order import OrderService, Order
                    order_service = OrderService()
                    
                    # Create a new pending buy order
                    new_order = Order(
                        username=st.session_state["username"],
                        ticker=ticker,
                        order_type="buy",  # This is a buy order
                        price=preis,      # Target price for execution
                        quantity=anteile,  # Number of shares
                        status="pending"   # Always start as pending
                    )
                    
                    # Add order via OrderService (which ensures it stays pending)
                    order_service.create_order(new_order)
                    
                    st.success(f"Buy order für {ticker} erstellt! Die Order wird ausgeführt wenn der aktuelle Preis unter oder gleich ${preis:.2f} ist.")
                    st.info("Du kannst den Status deiner Order im 'Stock Assistant' Tab unter 'Automated Trading' einsehen.")
                    st.rerun()
                else:
                    st.error(f"Ticker '{ticker}' konnte nicht validiert werden. Bitte überprüfe das Symbol.")

    # Tab 2: Add historical position
    with tab2:
        st.info("Hier kannst du historische Positionen direkt ins Portfolio hinzufügen. Die Preise werden automatisch validiert.")
        
        # Form to add historical position
        with st.form("historical_form"):
            st.subheader("Historische Position hinzufügen")
            hist_ticker = st.text_input("Ticker (z. B. AAPL)", key="hist_ticker").upper()
            hist_shares = st.number_input("Anzahl der Anteile", min_value=0.0, value=1.0, key="hist_shares")
            hist_price = st.number_input("Einstiegspreis ($)", min_value=0.0, value=0.0, key="hist_price")
            hist_date = st.date_input("Kaufdatum", value=date.today(), key="hist_date")
            
            hist_submitted = st.form_submit_button("Direkt ins Portfolio hinzufügen")

            if hist_submitted and hist_ticker and hist_shares > 0 and hist_price > 0:
                # Validate ticker
                if not StockService.validate_ticker(hist_ticker):
                    st.error(f"Ticker '{hist_ticker}' konnte nicht validiert werden. Bitte überprüfe das Symbol.")
                    st.stop()
                
                # Validate historical price
                valid_price = False
                try:
                    # Get historical data
                    st.info(f"Suche historische Daten für {hist_ticker} am {hist_date}...")
                    hist_data = yf.download(hist_ticker, 
                                          start=hist_date - timedelta(days=1), 
                                          end=hist_date + timedelta(days=2),
                                          progress=False)
                    
                    # Show a snippet of the data
                    if not hist_data.empty:
                        st.success(f"Historische Daten gefunden für {hist_ticker}")
                        with st.expander("Verfügbare Daten (Klick zum Anzeigen)"):
                            st.dataframe(hist_data.head())
                        # Convert the date index to string format for safer comparison
                        date_str = hist_date.strftime('%Y-%m-%d')
                        hist_data_dates = [idx.strftime('%Y-%m-%d') for idx in hist_data.index]
                        
                        # Get price range for that day
                        if date_str in hist_data_dates:
                            # Find the data for the specific date
                            day_data = hist_data[hist_data.index.strftime('%Y-%m-%d') == date_str]
                            # Ensure we extract numeric values, not pandas Series
                            day_low = float(day_data['Low'].iloc[0])
                            day_high = float(day_data['High'].iloc[0])
                            
                            # Debug info
                            st.info(f"Preisbereich am {hist_date}: ${day_low:.2f} - ${day_high:.2f}")
                            
                            # Check if the given price was within the day's range
                            if day_low <= hist_price <= day_high:
                                valid_price = True
                                # Directly add position to portfolio
                                portfolio_service.add_position(
                                    ticker=hist_ticker,
                                    shares=hist_shares,
                                    entry_price=hist_price,
                                    purchase_date=hist_date.strftime('%Y-%m-%d')
                                )
                                st.success(f"Position für {hist_ticker} wurde direkt zum Portfolio hinzugefügt!")
                                st.rerun()
                            else:
                                st.error(f"Der angegebene Preis ${hist_price:.2f} war am {hist_date} nicht im Preisbereich des Tickers.")
                                st.info(f"Der Preis am {hist_date} lag zwischen ${day_low:.2f} und ${day_high:.2f}.")
                        else:
                            st.error(f"Keine Daten für {hist_ticker} am {hist_date} gefunden. Bitte wähle einen gültigen Handelstag.")
                            weekday = hist_date.weekday()
                            if weekday >= 5:  # 5=Saturday, 6=Sunday
                                st.warning(f"Das gewählte Datum ist ein {'Samstag' if weekday == 5 else 'Sonntag'}. Börsen sind am Wochenende geschlossen.")
                            
                            # Show available dates
                            if not hist_data.empty:
                                available_dates = [idx.strftime('%Y-%m-%d') for idx in hist_data.index]
                                st.info(f"Verfügbare Handelstage in diesem Zeitraum: {', '.join(available_dates)}")
                    else:
                        st.error(f"Keine Daten für {hist_ticker} am {hist_date} gefunden. Bitte überprüfe den Ticker oder wähle ein anderes Datum.")
                except Exception as e:
                    st.error(f"Fehler bei der Überprüfung des historischen Preises: {str(e)}")
                    # Optional: Debug-Toggle für mehr Details
                    if st.checkbox("Debug-Informationen anzeigen"):
                        import traceback
                        st.code(traceback.format_exc())

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
