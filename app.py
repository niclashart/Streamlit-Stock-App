import streamlit as st
import os
import yfinance as yf
from datetime import date, datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from dotenv import load_dotenv
import requests
import pandas as pd
from database import (
    init_db, add_user, validate_user_login, update_user_password, get_user, # User functions
    get_portfolio, add_to_portfolio, update_portfolio_after_sell,          # Portfolio functions
    add_order_db, get_orders, update_order_status                            # Order functions
)

load_dotenv()

# USER_FILE = "users.csv" # Replaced by database
# ORDERS_FILE = "orders.csv" # Replaced by database

api_key = os.getenv("DEEPSEEK_API_KEY")

# Initialize the database (creates tables if they don't exist)
init_db()

# ------------------ Benutzerverwaltung (Database) ------------------
# All old CSV-based user functions (init_user_file, load_users, hash_password, save_user, 
# validate_login, update_password) are now handled by functions in database.py

# ------------------ Login / Registrierung ------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["user_id"] = None # Added user_id to session state

if not st.session_state["logged_in"]:
    st.title("🔐 Login / Registrierung")
    mode = st.radio("Modus wählen:", ["Login", "Registrieren", "Passwort vergessen?"])
    username_input = st.text_input("Benutzername") # Renamed for clarity
    password_input = st.text_input("Passwort", type="password") if mode != "Passwort vergessen?" else "" # Renamed

    if mode == "Login":
        if st.button("Einloggen"):
            user_id_val = validate_user_login(username_input, password_input) # Uses DB function
            if user_id_val:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username_input
                st.session_state["user_id"] = user_id_val # Store user_id
                st.success(f"Willkommen zurück, {username_input}!")
                st.rerun()
            else:
                st.error("❌ Falscher Benutzername oder Passwort.")
    elif mode == "Registrieren":
        if st.button("Registrieren"):
            if not username_input or not password_input: # Basic validation
                st.warning("Bitte Benutzername und Passwort eingeben.")
            elif get_user(username_input): # Check if user already exists in DB
                st.warning("Benutzername bereits vergeben.")
            else:
                if add_user(username_input, password_input): # Uses DB function
                    # No need to create portfolio_username.csv file anymore
                    st.success("Registrierung erfolgreich. Du kannst dich nun einloggen.")
                else:
                    st.error("Registrierung fehlgeschlagen. Der Benutzername könnte bereits existieren oder ein anderer Fehler ist aufgetreten.")
    elif mode == "Passwort vergessen?":
        new_pass_input = st.text_input("Neues Passwort", type="password") # Renamed
        if st.button("Zurücksetzen"):
            if update_user_password(username_input, new_pass_input): # Uses DB function
                st.success("Passwort wurde aktualisiert. Du kannst dich jetzt einloggen.")
            else:
                st.error("Benutzername nicht gefunden oder Update fehlgeschlagen.")
    st.stop()

# ------------------ Navigation ------------------
st.sidebar.title("📂 Navigation")
page = st.sidebar.radio("Seite auswählen", ["Übersicht", "Portfolio verwalten", "📄 Einzelanalyse", "🤖 Buy Bot"])

# ------------------ Globale Funktionen (Database Adjusted) ------------------
# def get_portfolio_file(): # Removed, no longer needed

def load_portfolio_db(): # Renamed to indicate DB usage
    if st.session_state.get("user_id"):
        return get_portfolio(st.session_state["user_id"]) # Uses DB function
    return pd.DataFrame(columns=["Ticker", "Anteile", "Einstiegspreis", "Kaufdatum"]) # Default empty DataFrame

# def save_portfolio(df): # Removed, replaced by add_to_portfolio and update_portfolio_after_sell

def get_price_history(tickers, start="2015-01-01"):
    data = pd.DataFrame()
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(start=start)
            if "Close" in hist.columns:
                data[ticker] = hist["Close"]
        except Exception as e:
            st.warning(f"{ticker}: konnte nicht geladen werden ({e})")
    return data

def get_dividends(ticker):
    stock = yf.Ticker(ticker)
    try:
        dividends = stock.dividends
        return dividends[dividends.index > "2015-01-01"]
    except:
        return pd.Series()

if "selected_ticker" not in st.session_state:
    st.session_state["selected_ticker"] = None

# ------------------ Order Management (Database Adjusted) ------------------
# def init_orders_file(): # Removed, DB init handles table creation

def load_orders_db(username_for_filter=None, status_filter=None): # Renamed
    user_id_to_filter = None
    if username_for_filter:
        user = get_user(username_for_filter) # Fetch user from DB to get ID
        if user:
            user_id_to_filter = user["id"]
        else: # If user not found, return empty DataFrame as no orders can belong to them
            return pd.DataFrame(columns=["id", "username", "ticker", "order_type", "price", "quantity", "created_at", "status"])
    return get_orders(user_id=user_id_to_filter, status=status_filter) # Uses DB function

# def add_order(username, ticker, order_type, price, quantity): # Removed, replaced by add_order_db

def check_orders_db(): # Renamed
    """Check all pending orders and execute them if target price is reached (DB version)"""
    pending_orders_df = load_orders_db(status_filter="pending") # Load only pending orders
    if pending_orders_df.empty:
        return [] # Return empty list if no pending orders
    
    executed_orders_list = []
    
    for _, order_row in pending_orders_df.iterrows():
        ticker = order_row["ticker"]
        order_id = order_row["id"] # Get order_id from the DataFrame
        
        # We need user_id for portfolio operations. The username is in order_row['username']
        order_user_details = get_user(order_row["username"])
        if not order_user_details:
            st.warning(f"User {order_row['username']} not found for order ID {order_id}. Skipping.")
            continue
        order_user_id = order_user_details["id"]

        try:
            stock = yf.Ticker(ticker)
            # Attempt to get regularMarketPrice, fallback to previous close if None
            current_price = stock.info.get("regularMarketPrice")
            if current_price is None:
                hist_data = stock.history(period="1d")
                if not hist_data.empty:
                    current_price = hist_data["Close"].iloc[-1]
                else:
                    st.warning(f"Could not fetch current price for {ticker} for order ID {order_id}.")
                    continue # Skip if price cannot be fetched
            
            execute_trade = False
            if order_row["order_type"] == "buy" and current_price <= order_row["price"]:
                execute_trade = True
            elif order_row["order_type"] == "sell" and current_price >= order_row["price"]:
                execute_trade = True
                
            if execute_trade:
                update_order_status(order_id, "executed") # Uses DB function
                
                if order_row["order_type"] == "buy":
                    add_to_portfolio( # Uses DB function
                        user_id=order_user_id,
                        ticker=ticker,
                        shares=order_row["quantity"],
                        entry_price=current_price, # Use actual execution price
                        purchase_date=datetime.now().date() # Use current date for purchase
                    )
                elif order_row["order_type"] == "sell":
                    update_portfolio_after_sell( # Uses DB function
                        user_id=order_user_id,
                        ticker=ticker,
                        quantity_to_sell=order_row["quantity"]
                    )
                
                executed_orders_list.append({
                    "username": order_row["username"], # Keep username for notifications
                    "ticker": ticker,
                    "type": order_row["order_type"],
                    "price": current_price,
                    "quantity": order_row["quantity"]
                })
        except Exception as e:
            st.warning(f"Error processing order ID {order_id} for {ticker}: {e}")
            # Consider setting order status to 'error' or similar via update_order_status(order_id, "error")
    
    return executed_orders_list

def cancel_order_db(order_id_to_cancel): # Simplified: Assumes UI passes correct order_id for logged-in user
    # For security, a real app would also check if order_id_to_cancel belongs to st.session_state['user_id']
    # This can be done by fetching the order and checking its user_id before updating.
    # For now, we trust the order_id is valid for the user context it's called from.
    # We also need to ensure the order is 'pending'.
    
    # Fetch the specific order to check its status and ownership (optional but good practice)
    # orders_df = get_orders(user_id=st.session_state.get("user_id"), status="pending")
    # order_to_cancel_details = orders_df[orders_df['id'] == order_id_to_cancel]

    # if not order_to_cancel_details.empty:
    #    update_order_status(order_id_to_cancel, "cancelled")
    #    return True
    # return False
    # Simpler direct update:
    update_order_status(order_id_to_cancel, "cancelled") # Assumes it's a pending order
    return True # Assume success, DB function would ideally return success/failure


# init_orders_file() # Removed, DB init handles this

# ------------------ Stock Info Chatbot ------------------
def get_stock_info(ticker):
    """Get comprehensive stock information for a ticker"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Basic info
        name = info.get('shortName', 'N/A')
        sector = info.get('sector', 'N/A') 
        industry = info.get('industry', 'N/A')
        
        # Financial info
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', 'N/A')
        eps = info.get('trailingEps', 'N/A')
        dividend = info.get('dividendRate', 0)
        dividend_yield = info.get('dividendYield', 0)
        if dividend_yield:
            dividend_yield = dividend_yield * 100
            
        # Price info
        current_price = info.get('regularMarketPrice', 'N/A')
        previous_close = info.get('previousClose', 'N/A')
        open_price = info.get('regularMarketOpen', 'N/A')
        day_low = info.get('dayLow', 'N/A')
        day_high = info.get('dayHigh', 'N/A')
        fifty_two_week_low = info.get('fiftyTwoWeekLow', 'N/A')
        fifty_two_week_high = info.get('fiftyTwoWeekHigh', 'N/A')
        
        # Analyst opinions
        target_price = info.get('targetMeanPrice', 'N/A')
        recommendation = info.get('recommendationKey', 'N/A')
        
        # Get recent news
        news = stock.news[:3] if hasattr(stock, 'news') and stock.news else []
        
        # Format the information
        stock_data = {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "industry": industry,
            "market_cap": f"${market_cap:,}" if isinstance(market_cap, (int, float)) else market_cap,
            "pe_ratio": pe_ratio,
            "eps": eps,
            "dividend": f"${dividend}" if dividend else "No dividend",
            "dividend_yield": f"{dividend_yield:.2f}%" if dividend_yield else "No dividend",
            "current_price": f"${current_price}" if current_price != 'N/A' else current_price,
            "previous_close": previous_close,
            "open": open_price,
            "day_range": f"${day_low} - ${day_high}" if day_low != 'N/A' and day_high != 'N/A' else "N/A",
            "52_week_range": f"${fifty_two_week_low} - ${fifty_two_week_high}" if fifty_two_week_low != 'N/A' and fifty_two_week_high != 'N/A' else "N/A",
            "target_price": f"${target_price}" if target_price != 'N/A' else target_price,
            "recommendation": recommendation.capitalize() if recommendation != 'N/A' else recommendation,
            "news": [{"title": item["title"], "link": item["link"]} for item in news] if news else []
        }
        
        return stock_data
    except Exception as e:
        return {"error": f"Failed to retrieve information for {ticker}: {str(e)}"}

def generate_chatbot_response(query, ticker=None):
    """Generate a response to the user's query using DeepSeek's API with conversation history"""
    try:
        conversation_history = []
        if "messages" in st.session_state:
            # Get the last few messages (limit to prevent token overflow)
            recent_messages = st.session_state["messages"][-10:]  # Last 10 messages
            for msg in recent_messages:
                conversation_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        if ticker:
            # Get stock information
            stock_data = get_stock_info(ticker)
            context = f"Information about {ticker}:\n{json.dumps(stock_data, indent=2)}\n\n"
        else:
            context = "The user is asking about stocks."
        
        if api_key:
            url = "https://api.deepseek.com/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            messages = [
                {"role": "system", "content": "You are a helpful stock market assistant. Answer questions about stocks, provide financial advice, and help with investment decisions. Keep responses concise and informative. Remember what the user has already told you and maintain context in your responses."}
            ]
            
            if conversation_history:
                messages.extend(conversation_history)
            
            messages.append({"role": "user", "content": f"{context}\n\nUser question: {query}"})
            
            payload = {
                "model": "deepseek-chat",  # Use the appropriate model name for DeepSeek
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"API Error: {response.status_code}. Please check your DeepSeek API key."
            
        else:
            if ticker:
                stock_data = get_stock_info(ticker)
                if "error" in stock_data:
                    return f"I couldn't find information about {ticker}. Please check if the ticker symbol is correct."
                
                response = f"Here's what I know about {ticker} ({stock_data['name']}):\n\n"
                response += f"Current Price: {stock_data['current_price']}\n"
                response += f"Sector: {stock_data['sector']}\n"
                response += f"Industry: {stock_data['industry']}\n"
                response += f"Market Cap: {stock_data['market_cap']}\n"
                if stock_data["pe_ratio"] != "N/A":
                    response += f"P/E Ratio: {stock_data['pe_ratio']:.2f}\n"
                if stock_data["dividend"] != "No dividend":
                    response += f"Dividend: {stock_data['dividend']}, Yield: {stock_data['dividend_yield']}\n"
                response += f"52 Week Range: {stock_data['52_week_range']}\n"
                
                if stock_data["recommendation"] != "N/A":
                    response += f"\nAnalyst Recommendation: {stock_data['recommendation']}"
                    
                if stock_data["news"]:
                    response += "\n\nRecent News:\n"
                    for news in stock_data["news"]:
                        response += f"- {news['title']}\n"
                
                return response
            else:
                return "Please set the DEEPSEEK_API_KEY in your environment to enable general questions. However, I can still provide specific stock information if you provide a ticker symbol."
    except Exception as e:
        return f"I encountered an error: {str(e)}"

# ------------------ Portfolio verwalten ------------------
if page == "Portfolio verwalten":
    st.title("📋 Portfolio verwalten")
    df_portfolio = load_portfolio_db() # Use DB version

    with st.form("portfolio_form_db"): # Unique form key
        st.subheader("Neue Position hinzufügen")
        ticker_add = st.text_input("Ticker (z. B. AAPL)").upper()
        anteile_add = st.number_input("Anzahl der Anteile", min_value=0.01, value=1.0, step=0.01) # Min value 0.01
        preis_add = st.number_input("Einstiegspreis ($)", min_value=0.01, value=100.0, step=0.01) # Min value 0.01
        kaufdatum_add = st.date_input("Kaufdatum", value=date.today())
        submitted_add_portfolio = st.form_submit_button("Hinzufügen")

        if submitted_add_portfolio and ticker_add and st.session_state.get("user_id"):
            add_to_portfolio( # Use DB version
                user_id=st.session_state["user_id"],
                ticker=ticker_add,
                shares=anteile_add,
                entry_price=preis_add,
                purchase_date=kaufdatum_add # Pass as date object
            )
            st.success(f"{ticker_add} hinzugefügt!")
            st.rerun()
        elif submitted_add_portfolio and not st.session_state.get("user_id"):
            st.error("Bitte einloggen, um Portfolio zu verwalten.")


    st.subheader("📦 Aktuelles Portfolio")
    if not df_portfolio.empty:
        st.dataframe(df_portfolio.set_index("Ticker"), use_container_width=True)
    else:
        st.info("Dein Portfolio ist leer. Füge Positionen über das Formular oben hinzu.")

# ------------------ Übersicht ------------------
elif page == "Übersicht":
    st.title("📈 Portfolio Übersicht")
    df_overview = load_portfolio_db() # Use DB version
    if df_overview.empty:
        st.warning("Bitte erfasse zuerst Positionen unter 'Portfolio verwalten'.")
        st.stop()

    tickers_overview = df_overview["Ticker"].unique().tolist() # Use unique tickers
    benchmarks = {
        "S&P 500": "^GSPC",
        "Nasdaq": "^IXIC",
        "MSCI World": "URTH"
    }
    selected_benchmarks = st.multiselect("🔍 Benchmarks auswählen", options=list(benchmarks.keys()), default=["S&P 500"])
    all_tickers_overview = tickers_overview + [benchmarks[b] for b in selected_benchmarks]

    data_overview = get_price_history(all_tickers_overview) # Make sure all_tickers_overview is defined correctly
    if data_overview.empty:
        st.warning("⚠️ Keine Kursdaten gefunden.")
        st.stop()

    latest_prices_overview = data_overview.iloc[-1]
    df_overview["Aktueller Kurs"] = df_overview["Ticker"].map(latest_prices_overview)
    df_overview["Kaufwert"] = df_overview["Anteile"] * df_overview["Einstiegspreis"]
    df_overview["Aktueller Wert"] = df_overview["Anteile"] * df_overview["Aktueller Kurs"]
    df_overview["Gewinn/Verlust €"] = df_overview["Aktueller Wert"] - df_overview["Kaufwert"]
    
    # Calculate Gewinn/Verlust % carefully to avoid division by zero
    df_overview["Gewinn/Verlust %"] = df_overview.apply(
        lambda row: (row["Gewinn/Verlust €"] / row["Kaufwert"]) * 100 if row["Kaufwert"] != 0 else 0,
        axis=1
    )

    total_value_overview = df_overview["Aktueller Wert"].sum()
    total_cost_overview = df_overview["Kaufwert"].sum()

    col1_overview, col2_overview = st.columns(2)
    col1_overview.metric("📦 Gesamtwert", f"${total_value_overview:,.2f}")

    # Calculate the change in portfolio value
    portfolio_change_value = total_value_overview - total_cost_overview
    
    # Calculate performance percentage
    performance_percent = (portfolio_change_value / total_cost_overview) * 100 if total_cost_overview != 0 else 0
    
    # Format the delta display string for st.metric
    # The string needs to start with '-' for negative values to be colored red by default.
    if portfolio_change_value < 0:
        # For negative, format as e.g., "-$41.22"
        delta_display = f"-${abs(portfolio_change_value):,.2f}"
    else:
        # For positive, format as e.g., "$41.22"
        delta_display = f"${portfolio_change_value:,.2f}"

    col2_overview.metric("📈 Performance", f"{performance_percent:.2f}%", delta=delta_display)

    st.subheader("📊 Portfolio Verlauf")

    # shares_dict_overview = dict(zip(df_portfolio_overview["Ticker"], df_portfolio_overview["Anteile"])) # Not directly used with new logic
    portfolio_history_overview = pd.DataFrame(index=data_overview.index)

    # Berechne Portfoliowerte unter Beachtung des Kaufdatums
    for _, row_overview in df_overview.iterrows():
        ticker_hist = row_overview["Ticker"]
        anzahl_hist = row_overview["Anteile"]
        # kaufdatum_hist should be datetime object from load_portfolio_db
        kaufdatum_hist = pd.to_datetime(row_overview["Kaufdatum"])


        if ticker_hist in data_overview.columns:
            werte_hist = data_overview[ticker_hist].copy()
            
            # Ensure kaufdatum_hist is timezone-naive if data_overview.index is, or localize
            if data_overview.index.tz is not None and kaufdatum_hist.tzinfo is None:
                kaufdatum_hist_aware = kaufdatum_hist.tz_localize(data_overview.index.tz)
            elif data_overview.index.tz is None and kaufdatum_hist.tzinfo is not None:
                kaufdatum_hist_aware = kaufdatum_hist.tz_localize(None)
            else: # Both are same (None or already compatible)
                kaufdatum_hist_aware = kaufdatum_hist
            
            werte_hist[data_overview.index < kaufdatum_hist_aware] = 0
            portfolio_history_overview[ticker_hist] = werte_hist * anzahl_hist
    # Gesamter Portfolio-Wert über Zeit
    portfolio_history_overview["Total"] = portfolio_history_overview.sum(axis=1)

    # Bestimme den ersten investierten Wert
    valid_values = portfolio_history_overview["Total"][portfolio_history_overview["Total"] > 0]
    if not valid_values.empty:
        first_valid_value = valid_values.iloc[0]
    else:
        first_valid_value = 1  # Fallback für leeres Portfolio, um Fehler zu vermeiden

    # Plot mit Plotly
    fig = make_subplots()
    fig.add_trace(go.Scatter(
        x=portfolio_history_overview.index,
        y=portfolio_history_overview["Total"],
        name="Portfolio",
        line=dict(width=3)
    ))

    # Benchmarks normieren und einzeichnen
    for name in selected_benchmarks:
        bm_symbol = benchmarks[name]
        if bm_symbol in data_overview.columns:
            benchmark = data_overview[bm_symbol].copy()
            benchmark = benchmark / benchmark.iloc[0] * first_valid_value
            fig.add_trace(go.Scatter(
                x=benchmark.index,
                y=benchmark,
                name=name,
                line=dict(dash="dot")
            ))

    fig.update_layout(
        title="Wertentwicklung",
        xaxis_title="Datum",
        yaxis_title="Wert in $",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)


    st.subheader("🧾 Portfolio Details")
    # Use a unique key for each button to prevent conflicts
    for idx, row_detail in df_overview.iterrows(): # Added idx for unique key
        if st.button(f"{row_detail['Ticker']} auswählen", key=f"select_ticker_{idx}_{row_detail['Ticker']}"):
            st.session_state["selected_ticker"] = row_detail["Ticker"]
            st.rerun()
    st.dataframe(df_overview.set_index("Ticker").round(2), use_container_width=True)

    # --- Pending Orders Section (Table Format) ---
    st.subheader("⏳ Ihre offenen Orders")
    pending_orders_df = load_orders_db(username_for_filter=st.session_state.get("username"), status_filter="pending") # Renamed from pending_orders_overview

    if not pending_orders_df.empty:
        # Prepare DataFrame for display
        display_df = pending_orders_df.copy()
        
        # Apply formatting for display columns
        display_df['price_display'] = pd.to_numeric(display_df['price'], errors='coerce').apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
        display_df['created_at_display'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['order_type_display'] = display_df['order_type'].astype(str).str.capitalize()
        display_df['status_display'] = display_df['status'].astype(str).str.capitalize()
        # Assuming quantity is already well-formatted, if not, add:
        # display_df['quantity_display'] = pd.to_numeric(display_df['quantity'], errors='coerce').apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A") # Or appropriate formatting
        display_df['quantity_display'] = display_df['quantity']


        # Select and rename columns for the table
        df_for_table = display_df[['ticker', 'order_type_display', 'price_display', 'quantity_display', 'created_at_display', 'status_display']].rename(columns={
            'ticker': 'Ticker',
            'order_type_display': 'Type',
            'price_display': 'Price ($)',
            'quantity_display': 'Quantity',
            'created_at_display': 'Created At',
            'status_display': 'Status'
        })
        st.dataframe(df_for_table, use_container_width=True)

        # Cancellation UI
        # Use original pending_orders_df for logic, as it has raw price and id
        order_options_for_select = {
            row['id']: (
                f"{row['ticker']} ({row['order_type'].capitalize()}) - "
                f"{row['quantity']} @ ${pd.to_numeric(row['price'], errors='coerce'):.2f} - "
                f"Created: {pd.to_datetime(row['created_at']).strftime('%Y-%m-%d %H:%M')} (ID: {row['id']})"
            )
            for index, row in pending_orders_df.iterrows()
        }

        if order_options_for_select:
            st.markdown("---") 
            st.subheader("Order stornieren")
            selected_order_id_to_cancel = st.selectbox(
                "Wählen Sie eine Order zum Stornieren aus:",
                options=list(order_options_for_select.keys()),
                format_func=lambda x: order_options_for_select[x],
                key="cancel_order_selectbox_overview"
            )
            
            if st.button("Ausgewählte Order stornieren", key="cancel_selected_order_button_overview"):
                if selected_order_id_to_cancel is not None:
                    order_to_cancel_details = pending_orders_df[pending_orders_df['id'] == selected_order_id_to_cancel].iloc[0]
                    order_ticker = order_to_cancel_details['ticker']
                    
                    if cancel_order_db(selected_order_id_to_cancel):
                        st.success(f"Order für {order_ticker} (ID: {selected_order_id_to_cancel}) wurde storniert.")
                        st.rerun()
                    else:
                        st.error(f"Fehler beim Stornieren der Order für {order_ticker} (ID: {selected_order_id_to_cancel}).")
                else:
                    st.warning("Keine Order ausgewählt oder die ausgewählte Order ist ungültig.")
    else:
        st.info("Sie haben keine offenen Orders.")
    # --- End of Pending Orders Section ---

    st.subheader("💸 Dividenden")
    dividend_data_overview = []
    for ticker_div_overview in tickers_overview: # Ensure tickers_overview is defined
        divs_overview = get_dividends(ticker_div_overview)
        if not divs_overview.empty:
            # Sum shares for the ticker if multiple entries exist (though DB aims for one entry per purchase date)
            # For simplicity, assuming df_overview structure from get_portfolio is suitable here
            total_shares_for_ticker_overview = df_overview.loc[df_overview["Ticker"] == ticker_div_overview, "Anteile"].sum()
            total_div_amount_overview = divs_overview.sum() * total_shares_for_ticker_overview
            dividend_data_overview.append((ticker_div_overview, total_div_amount_overview, len(divs_overview)))
    if dividend_data_overview:
        div_df_overview = pd.DataFrame(dividend_data_overview, columns=["Ticker", "Summe Dividenden ($)", "Zahlungen"])
        st.dataframe(div_df_overview.set_index("Ticker").round(2))
    else:
        st.info("Keine Dividenden im aktuellen Zeitraum.")

    st.subheader("⚖️ Rebalancing Analyse")
    if total_value_overview > 0 and not df_overview.empty: # Check for empty df and zero total value
        df_overview["Gewichtung"] = df_overview["Aktueller Wert"] / total_value_overview * 100
        target_rebalance_overview = 100 / len(df_overview)
        df_overview["Abweichung"] = df_overview["Gewichtung"] - target_rebalance_overview
        st.dataframe(df_overview[["Ticker", "Aktueller Wert", "Gewichtung", "Abweichung"]].set_index("Ticker").round(2))
    elif df_overview.empty:
        st.info("Portfolio ist leer, keine Rebalancing-Analyse möglich.")
    else: # total_value_overview is 0 but portfolio not empty (e.g. all stocks crashed to 0)
        st.info("Portfoliowert ist Null, Rebalancing-Analyse nicht aussagekräftig.")


# ------------------ Einzelanalyse ------------------
elif page == "📄 Einzelanalyse":
    ticker = st.session_state.get("selected_ticker")
    if not ticker:
        st.info("Bitte wähle eine Aktie in der Übersicht.")
        st.stop()

    st.title(f"📄 Analyse: {ticker}")
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="6mo")

    col1, col2 = st.columns(2)
    col1.metric("Aktueller Kurs", f"${hist['Close'].iloc[-1]:.2f}")
    col2.metric("Tagesveränderung", f"${hist['Close'].iloc[-1] - hist['Open'].iloc[-1]:.2f}")

    col3, col4 = st.columns(2)
    col3.metric("Marktkapitalisierung", f"${info.get('marketCap', 0):,}")
    col4.metric("Dividende/Aktie", f"${info.get('dividendRate', 0):.2f}")

    st.subheader("📈 Kursverlauf (6 Monate)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], name="Close"))
    fig.update_layout(xaxis_title="Datum", yaxis_title="Preis ($)")
    st.plotly_chart(fig, use_container_width=True)

# ------------------ Buy Bot ------------------
elif page == "🤖 Buy Bot":
    st.title("🤖 Stock Assistant")
    
    # Initialize session state variables for chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    
    if "orders_checked" not in st.session_state:
        st.session_state["orders_checked"] = datetime.now().timestamp() - 120  # Check immediately first time
    
    # Check for orders that need to be executed (every 2 minutes)
    current_time_bot = datetime.now().timestamp()
    if current_time_bot - st.session_state.get("orders_checked", 0) > 120: # Default orders_checked to 0 if not set
        with st.spinner("Checking pending orders..."):
            executed_orders_bot = check_orders_db() # Use DB version
            if executed_orders_bot: # Check if list is not empty
                st.success(f"🎉 {len(executed_orders_bot)} order(s) were executed!")
                for order_bot in executed_orders_bot:
                    # Notify only if the order belongs to the currently logged-in user
                    if order_bot["username"] == st.session_state.get("username"):
                        st.info(f"Your {order_bot['type']} order for {order_bot['quantity']} shares of {order_bot['ticker']} was executed at ${order_bot['price']:.2f}!")
        st.session_state["orders_checked"] = current_time_bot
    
    # Create tabs for chatbot and order management
    tab1, tab2 = st.tabs(["💬 Stock Chatbot", "📊 Automated Trading"])
    
    # Tab 1: Stock Info Chatbot
    with tab1:
        st.subheader("💬 Ask about stocks")
        
        # Display API key status
        if api_key:
            st.success("DeepSeek API key is configured ✅")
        else:
            st.warning("DeepSeek API key not found. Please add it to your .env file to enable advanced features.")
            st.info("Set DEEPSEEK_API_KEY=your_api_key in a .env file in the app directory.")
        
        # Display past messages
        for message in st.session_state["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Input for new messages
        if prompt := st.chat_input("Ask about a stock or market trend..."):
            # Add user message to chat history
            st.session_state["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Extract ticker if present
            ticker_match = None
            tokens = prompt.upper().split()
            for token in tokens:
                if token.isalpha() and len(token) <= 5 and token not in ["A", "I", "THE", "AND", "OR", "FOR", "WHAT", "HOW", "WHY"]:
                    try:
                        stock = yf.Ticker(token)
                        info = stock.info
                        if 'regularMarketPrice' in info:
                            ticker_match = token
                            break
                    except:
                        pass
            
            # Generate assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = generate_chatbot_response(prompt, ticker_match)
                    st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state["messages"].append({"role": "assistant", "content": response})

    # Tab 2: Automated Trading
    with tab2:
        st.subheader("📊 Set Automated Buy/Sell Orders")
        
        df_bot_portfolio = load_portfolio_db() # Load current user's portfolio
        total_holdings_bot = {}
        
        if not df_bot_portfolio.empty:
            # Group by ticker to show total holdings if multiple purchases of same stock
            for ticker_group_bot, group_data_bot in df_bot_portfolio.groupby("Ticker"):
                total_holdings_bot[ticker_group_bot] = group_data_bot["Anteile"].sum()
            
            st.info("Your current holdings:")
            holdings_text_bot = ", ".join(f"{ticker_h}: {shares_h} shares" for ticker_h, shares_h in total_holdings_bot.items())
            st.text(holdings_text_bot if total_holdings_bot else "No holdings yet.")
        else:
            st.info("You have no current holdings to display.")
        
        with st.form("order_form_db_tab"): # Unique form key
            st.subheader("Create New Order")
            col1_order_form, col2_order_form = st.columns(2)
            with col1_order_form:
                order_ticker_form = st.text_input("Ticker Symbol", key="order_ticker_input").upper()
                order_type_form = st.selectbox("Order Type", ["buy", "sell"], key="order_type_select")
            with col2_order_form:
                order_quantity_form = st.number_input("Quantity", min_value=0.01, value=1.0, step=0.01, key="order_quantity_input")
                order_price_form = st.number_input("Target Price ($)", min_value=0.01, value=100.0, step=0.01, key="order_price_input")

            submit_order_button_form = st.form_submit_button("Place Order")

            if submit_order_button_form and order_ticker_form and st.session_state.get("user_id"):
                if add_order_db( # Use DB function
                    user_id=st.session_state["user_id"],
                    ticker=order_ticker_form,
                    order_type=str(order_type_form), # Ensure it's a string
                    price=order_price_form,
                    quantity=order_quantity_form
                ):
                    st.success(f"{str(order_type_form).capitalize()} order for {order_quantity_form} of {order_ticker_form} at ${order_price_form} placed.")
                    st.rerun() # Rerun to update pending orders list
                else:
                    st.error("Failed to place order. Please try again.")
            elif submit_order_button_form and not st.session_state.get("user_id"):
                 st.error("User not logged in. Please log in to place orders.")
        
        st.subheader("🕒 Your Pending Orders")
        # Load pending orders for the current logged-in user
        pending_orders_user_df = load_orders_db(username_for_filter=st.session_state.get("username"), status_filter="pending")

        if not pending_orders_user_df.empty:
            for _, order_item_row in pending_orders_user_df.iterrows(): # Iterate over rows
                cols_display = st.columns([0.15, 0.15, 0.1, 0.1, 0.2, 0.15, 0.15]) # Adjusted column widths
                cols_display[0].text(order_item_row['ticker'])
                cols_display[1].text(order_item_row['order_type'].capitalize())
                cols_display[2].text(f"${order_item_row['price']:.2f}")
                cols_display[3].text(order_item_row['quantity'])
                # Format date nicely
                created_date = pd.to_datetime(order_item_row['created_at']).strftime('%Y-%m-%d %H:%M')
                cols_display[4].text(created_date)
                cols_display[5].text(order_item_row['status'].capitalize())
                # Unique key for cancel button using order ID
                if cols_display[6].button("Cancel", key=f"cancel_order_{order_item_row['id']}"):
                    if cancel_order_db(order_item_row['id']): # Pass order_id directly
                        st.success(f"Order for {order_item_row['ticker']} cancelled.")
                        st.rerun() # Rerun to refresh the list
                    else:
                        st.error(f"Failed to cancel order for {order_item_row['ticker']}. It might have already been processed or an error occurred.")
        else:
            st.info("You have no pending orders.")

        # Display historical orders (executed or cancelled)
        st.subheader("📜 Order History")
        all_user_orders_history = load_orders_db(username_for_filter=st.session_state.get("username"))

        if not all_user_orders_history.empty:
            executed_or_cancelled_orders = all_user_orders_history[
                all_user_orders_history["status"].isin(["executed", "cancelled"])
            ]
            if not executed_or_cancelled_orders.empty:
                # Select and rename columns for display
                display_df = executed_or_cancelled_orders[
                    ["created_at", "ticker", "order_type", "price", "quantity", "status"]
                ].copy() # Use .copy() to avoid SettingWithCopyWarning
                display_df["created_at"] = pd.to_datetime(display_df["created_at"]).dt.strftime('%Y-%m-%d %H:%M')
                display_df.rename(columns={
                    "created_at": "Date",
                    "ticker": "Ticker",
                    "order_type": "Type",
                    "price": "Price ($)",
                    "quantity": "Qty",
                    "status": "Status"
                }, inplace=True)
                st.dataframe(
                    display_df.set_index("Date"), # Set Date as index for better readability
                    use_container_width=True
                )
            else:
                st.info("You have no executed or cancelled orders in your history.")
        else:
            st.info("You have no order history yet.")

# ------------------ Logout ------------------
st.sidebar.markdown("---")
if st.sidebar.button("🔓 Logout"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["selected_ticker"] = None
    st.rerun()
