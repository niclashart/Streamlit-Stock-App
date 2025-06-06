"""
Stock Portfolio Assistant - Frontend Application
"""
import streamlit as st
import pandas as pd
import requests
import os
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_URL = f"{API_BASE_URL}/api/v1"

# Set page configuration
st.set_page_config(
    page_title="Stock Portfolio Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state for user authentication
if "token" not in st.session_state:
    st.session_state.token = None

if "username" not in st.session_state:
    st.session_state.username = None

# API request functions
def api_get(endpoint, token=None):
    """Make GET request to API"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.get(f"{API_URL}{endpoint}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def api_post(endpoint, data, token=None):
    """Make POST request to API"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def api_delete(endpoint, token=None):
    """Make DELETE request to API"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.delete(f"{API_URL}{endpoint}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

# Authentication functions
def login(username, password):
    """Login to API and get token"""
    response = requests.post(
        f"{API_URL}/auth/token",
        data={"username": username, "password": password}
    )
    
    if response.status_code == 200:
        data = response.json()
        st.session_state.token = data["access_token"]
        st.session_state.username = username
        return True
    return False

def register(username, password):
    """Register new user"""
    response = requests.post(
        f"{API_URL}/auth/register",
        json={"username": username, "password": password}
    )
    
    if response.status_code == 200:
        return True
    return False

def logout():
    """Clear session state"""
    st.session_state.token = None
    st.session_state.username = None

# Authentication UI
def show_auth_ui():
    """Show login/register UI"""
    st.title("🔐 Login / Registrierung")
    
    tab1, tab2 = st.tabs(["Login", "Registrieren"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Benutzername")
            password = st.text_input("Passwort", type="password")
            submit = st.form_submit_button("Einloggen")
            
            if submit:
                if login(username, password):
                    st.success(f"Willkommen zurück, {username}!")
                    st.rerun()
                else:
                    st.error("❌ Falscher Benutzername oder Passwort.")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Neuer Benutzername")
            new_password = st.text_input("Neues Passwort", type="password")
            confirm_password = st.text_input("Passwort bestätigen", type="password")
            submit = st.form_submit_button("Registrieren")
            
            if submit:
                if new_password != confirm_password:
                    st.error("Passwörter stimmen nicht überein.")
                elif len(new_password) < 6:
                    st.error("Passwort muss mindestens 6 Zeichen lang sein.")
                else:
                    if register(new_username, new_password):
                        st.success("Registrierung erfolgreich. Du kannst dich nun einloggen.")
                    else:
                        st.error("Registrierung fehlgeschlagen. Benutzername existiert möglicherweise bereits.")

# Portfolio UI components
def show_portfolio_summary():
    """Show portfolio summary"""
    data = api_get("/portfolio/summary", st.session_state.token)
    
    if not data:
        st.warning("Keine Portfolio-Daten verfügbar.")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Gesamtwert", f"${data['total_value']:,.2f}")
    
    with col2:
        st.metric("Einstandswert", f"${data['total_cost']:,.2f}")
    
    with col3:
        gain_loss = data['total_gain_loss']
        arrow = "↑" if gain_loss >= 0 else "↓"
        st.metric("Gewinn/Verlust", f"${abs(gain_loss):,.2f}", f"{arrow} {data['total_gain_loss_percent']:.2f}%")
    
    with col4:
        st.metric("Positionen", len(data['positions']))
    
    # Portfolio table
    if data['positions']:
        df = pd.DataFrame(data['positions'])
        df = df.rename(columns={
            'ticker': 'Ticker',
            'shares': 'Anteile',
            'entry_price': 'Einstiegspreis',
            'current_price': 'Aktueller Preis',
            'current_value': 'Aktueller Wert',
            'cost_basis': 'Einstandswert',
            'gain_loss': 'G/V',
            'gain_loss_percent': 'G/V %',
            'purchase_date': 'Kaufdatum'
        })
        
        # Format columns
        df['Einstiegspreis'] = df['Einstiegspreis'].map('${:,.2f}'.format)
        df['Aktueller Preis'] = df['Aktueller Preis'].map('${:,.2f}'.format)
        df['Aktueller Wert'] = df['Aktueller Wert'].map('${:,.2f}'.format)
        df['Einstandswert'] = df['Einstandswert'].map('${:,.2f}'.format)
        df['G/V'] = df['G/V'].map('${:,.2f}'.format)
        df['G/V %'] = df['G/V %'].map('{:,.2f}%'.format)
        
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("Keine Positionen im Portfolio. Füge deine ersten Aktien hinzu!")

def add_position_form():
    """Form to add a new position"""
    with st.form("add_position"):
        st.subheader("Position hinzufügen")
        ticker = st.text_input("Ticker Symbol")
        shares = st.number_input("Anteile", min_value=0.01, step=0.01)
        entry_price = st.number_input("Einstiegspreis ($)", min_value=0.01, step=0.01)
        purchase_date = st.date_input("Kaufdatum")
        
        submit = st.form_submit_button("Hinzufügen")
        
        if submit:
            if ticker and shares > 0 and entry_price > 0:
                result = api_post(
                    "/portfolio/positions",
                    {
                        "ticker": ticker.upper(),
                        "shares": shares,
                        "entry_price": entry_price,
                        "purchase_date": purchase_date.strftime("%Y-%m-%d")
                    },
                    st.session_state.token
                )
                
                if result:
                    st.success(f"Position {ticker.upper()} hinzugefügt!")
                    st.rerun()
            else:
                st.error("Bitte fülle alle Felder korrekt aus.")

# Stock analysis components
def show_stock_analysis(ticker):
    """Show stock analysis for a specific ticker"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader(f"{ticker} Kursverlauf")
        period = st.selectbox(
            "Zeitraum",
            options=["1m", "3m", "6m", "1y", "2y", "5y", "max"],
            index=3
        )
        
        stock_history = api_get(f"/stocks/{ticker}/history?period={period}", st.session_state.token)
        
        if stock_history and stock_history.get('data'):
            df = pd.DataFrame(stock_history['data'])
            df['Date'] = pd.to_datetime(df['Date'])
            
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['Close'],
                    mode='lines',
                    name='Schlusskurs',
                    line=dict(color='royalblue', width=2)
                )
            )
            fig.update_layout(
                title=f"{ticker} Kursverlauf ({period})",
                xaxis_title="Datum",
                yaxis_title="Preis ($)",
                height=500,
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Keine Kursdaten für {ticker} verfügbar.")
    
    with col2:
        st.subheader("Fundamentaldaten")
        stock_info = api_get(f"/stocks/{ticker}", st.session_state.token)
        
        if stock_info:
            metrics = [
                ("Name", stock_info.get("name", "N/A")),
                ("Sektor", stock_info.get("sector", "N/A")),
                ("Preis", f"${stock_info.get('price', 0):.2f}"),
                ("Marktkapitalisierung", f"${stock_info.get('market_cap', 0)/1e9:.2f}B"),
                ("P/E-Ratio", f"{stock_info.get('pe_ratio', 0):.2f}"),
                ("EPS", f"${stock_info.get('eps', 0):.2f}"),
                ("Dividendenrendite", f"{stock_info.get('dividend_yield', 0):.2f}%"),
                ("Kursziel", f"${stock_info.get('target_price', 0):.2f}")
            ]
            
            for label, value in metrics:
                st.text(f"{label}: {value}")

# Trading UI components
def show_orders():
    """Show user's orders"""
    orders = api_get("/trading/orders", st.session_state.token)
    
    if not orders:
        st.warning("Keine Aufträge vorhanden.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(orders)
    if not df.empty:
        # Rename columns
        df = df.rename(columns={
            'ticker': 'Ticker',
            'order_type': 'Typ',
            'price': 'Preis',
            'quantity': 'Menge',
            'status': 'Status',
            'created_at': 'Erstellt am',
            'executed_at': 'Ausgeführt am'
        })
        
        # Format columns
        df['Typ'] = df['Typ'].map({'buy': 'Kauf', 'sell': 'Verkauf'})
        df['Preis'] = df['Preis'].map('${:,.2f}'.format)
        df['Status'] = df['Status'].map({
            'pending': '⏳ Ausstehend',
            'executed': '✅ Ausgeführt',
            'cancelled': '❌ Storniert'
        })
        df['Erstellt am'] = pd.to_datetime(df['Erstellt am']).dt.strftime('%Y-%m-%d %H:%M')
        df['Ausgeführt am'] = pd.to_datetime(df['Ausgeführt am'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
        
        # Replace NaN with -
        df = df.fillna('-')
        
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("Keine Aufträge vorhanden.")

def create_order_form():
    """Form to create a new trading order"""
    with st.form("create_order"):
        st.subheader("Neuen Handelsauftrag erstellen")
        
        ticker = st.text_input("Ticker Symbol")
        order_type = st.selectbox("Auftragstyp", options=["buy", "sell"], format_func=lambda x: "Kauf" if x == "buy" else "Verkauf")
        price = st.number_input("Preis ($)", min_value=0.01, step=0.01)
        quantity = st.number_input("Menge", min_value=0.01, step=0.01)
        
        submit = st.form_submit_button("Auftrag erstellen")
        
        if submit:
            if ticker and price > 0 and quantity > 0:
                result = api_post(
                    "/trading/orders",
                    {
                        "ticker": ticker.upper(),
                        "order_type": order_type,
                        "price": price,
                        "quantity": quantity
                    },
                    st.session_state.token
                )
                
                if result:
                    st.success(f"{order_type.capitalize()}-Auftrag für {ticker.upper()} erstellt!")
                    st.rerun()
            else:
                st.error("Bitte fülle alle Felder korrekt aus.")

# Chat UI component
def show_chat_ui():
    """Show chat UI for stock assistant"""
    st.subheader("KI-Aktien-Assistent")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    user_input = st.chat_input("Stelle eine Frage zu Aktien oder deinem Portfolio...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Show user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Send message to API
        response = api_post(
            "/chat",
            {
                "message": user_input,
                "conversation_history": st.session_state.chat_history
            },
            st.session_state.token
        )
        
        if response:
            assistant_response = response["response"]
            
            # Add assistant response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
            
            # Show assistant response
            with st.chat_message("assistant"):
                st.write(assistant_response)
        else:
            with st.chat_message("assistant"):
                st.write("Es tut mir leid, ich konnte keine Antwort erhalten. Bitte versuche es später erneut.")

# Main application
def main():
    """Main application function"""
    # Check if logged in
    if not st.session_state.token:
        show_auth_ui()
        return
    
    # Sidebar navigation
    st.sidebar.title("📂 Navigation")
    
    # User info
    st.sidebar.markdown(f"**Benutzer:** {st.session_state.username}")
    
    # Navigation options
    page = st.sidebar.radio(
        "Seiten",
        ["Portfolio", "Aktienanalyse", "Handelsaufträge", "KI-Assistent"]
    )
    
    # Logout button
    if st.sidebar.button("Ausloggen"):
        logout()
        st.rerun()
    
    # Page content
    if page == "Portfolio":
        st.title("📊 Mein Portfolio")
        show_portfolio_summary()
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            add_position_form()
    
    elif page == "Aktienanalyse":
        st.title("📈 Aktienanalyse")
        
        ticker = st.text_input("Ticker Symbol eingeben", value="AAPL").upper()
        if ticker:
            show_stock_analysis(ticker)
    
    elif page == "Handelsaufträge":
        st.title("💱 Handelsaufträge")
        
        tab1, tab2 = st.tabs(["Meine Aufträge", "Neuer Auftrag"])
        
        with tab1:
            show_orders()
        
        with tab2:
            create_order_form()
    
    elif page == "KI-Assistent":
        st.title("🤖 KI-Aktien-Assistent")
        show_chat_ui()

if __name__ == "__main__":
    main()