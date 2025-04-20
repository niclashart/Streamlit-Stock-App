import hashlib
import pandas as pd
import streamlit as st
import os
import yfinance as yf
from datetime import date, datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from dotenv import load_dotenv
import requests

load_dotenv()

USER_FILE = "users.csv"
ORDERS_FILE = "orders.csv"

api_key = os.getenv("DEEPSEEK_API_KEY")

# ------------------ Benutzerverwaltung ------------------
def init_user_file():
    if not os.path.exists(USER_FILE):
        df = pd.DataFrame(columns=["username", "password_hash"])
        df.to_csv(USER_FILE, index=False)

def load_users():
    return pd.read_csv(USER_FILE)

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def save_user(username, password):
    df = load_users()
    new_user = pd.DataFrame([{
        "username": username,
        "password_hash": hash_password(password)
    }])
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(USER_FILE, index=False)

def validate_login(username, password):
    df = load_users()
    if username in df["username"].values:
        hashed_pw = hash_password(password)
        return hashed_pw == df.loc[df["username"] == username, "password_hash"].values[0]
    return False

def update_password(username, new_password):
    df = load_users()
    if username in df["username"].values:
        df.loc[df["username"] == username, "password_hash"] = hash_password(new_password)
        df.to_csv(USER_FILE, index=False)
        return True
    return False

# ------------------ Login / Registrierung ------------------
init_user_file()
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""

if not st.session_state["logged_in"]:
    st.title("🔐 Login / Registrierung")
    mode = st.radio("Modus wählen:", ["Login", "Registrieren", "Passwort vergessen?"])
    username = st.text_input("Benutzername")
    password = st.text_input("Passwort", type="password") if mode != "Passwort vergessen?" else ""

    if mode == "Login":
        if st.button("Einloggen"):
            if validate_login(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Willkommen zurück, {username}!")
                st.rerun()
            else:
                st.error("❌ Falscher Benutzername oder Passwort.")
    elif mode == "Registrieren":
        if st.button("Registrieren"):
            df = load_users()
            if username in df["username"].values:
                st.warning("Benutzername bereits vergeben.")
            elif username == "" or password == "":
                st.warning("Bitte Benutzername und Passwort eingeben.")
            else:
                save_user(username, password)
                open(f"portfolio_{username}.csv", "w").write("Ticker,Anteile,Einstiegspreis,Kaufdatum\n")
                st.success("Registrierung erfolgreich. Du kannst dich nun einloggen.")
    elif mode == "Passwort vergessen?":
        new_pass = st.text_input("Neues Passwort", type="password")
        if st.button("Zurücksetzen"):
            if update_password(username, new_pass):
                st.success("Passwort wurde aktualisiert. Du kannst dich jetzt einloggen.")
            else:
                st.error("Benutzername nicht gefunden.")
    st.stop()

# ------------------ Navigation ------------------
st.sidebar.title("📂 Navigation")
page = st.sidebar.radio("Seite auswählen", ["Übersicht", "Portfolio verwalten", "📄 Einzelanalyse", "🤖 Buy Bot"])

# ------------------ Globale Funktionen ------------------
def get_portfolio_file():
    return f"portfolio_{st.session_state['username']}.csv"

def load_portfolio():
    file = get_portfolio_file()
    if os.path.exists(file):
        return pd.read_csv(file, parse_dates=["Kaufdatum"])
    return pd.DataFrame(columns=["Ticker", "Anteile", "Einstiegspreis", "Kaufdatum"])

def save_portfolio(df):
    df.to_csv(get_portfolio_file(), index=False)

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

# ------------------ Order Management ------------------
def init_orders_file():
    if not os.path.exists(ORDERS_FILE):
        df = pd.DataFrame(columns=["username", "ticker", "order_type", "price", "quantity", "created_at", "status"])
        df.to_csv(ORDERS_FILE, index=False)

def load_orders(username=None):
    if not os.path.exists(ORDERS_FILE):
        init_orders_file()
        
    df = pd.read_csv(ORDERS_FILE)
    if username:
        df = df[df["username"] == username]
    return df

def add_order(username, ticker, order_type, price, quantity):
    df = load_orders()
    new_order = pd.DataFrame([{
        "username": username,
        "ticker": ticker,
        "order_type": order_type,
        "price": price,
        "quantity": quantity,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending"
    }])
    df = pd.concat([df, new_order], ignore_index=True)
    df.to_csv(ORDERS_FILE, index=False)
    return True

def check_orders():
    """Check all pending orders and execute them if target price is reached"""
    df = load_orders()
    if df.empty or "pending" not in df["status"].values:
        return False
    
    pending_orders = df[df["status"] == "pending"]
    executed_orders = []
    
    for _, order in pending_orders.iterrows():
        ticker = order["ticker"]
        try:
            # Get current price
            stock = yf.Ticker(ticker)
            current_price = stock.info["regularMarketPrice"]
            
            # Check if order should be executed
            execute = False
            if order["order_type"] == "buy" and current_price <= order["price"]:
                execute = True
            elif order["order_type"] == "sell" and current_price >= order["price"]:
                execute = True
                
            if execute:
                # Update order status
                df.loc[(df["username"] == order["username"]) & 
                       (df["ticker"] == order["ticker"]) & 
                       (df["created_at"] == order["created_at"]), "status"] = "executed"
                
                # If this is a buy order, add to portfolio
                if order["order_type"] == "buy":
                    user_portfolio = load_portfolio() if order["username"] == st.session_state["username"] else pd.read_csv(f"portfolio_{order['username']}.csv")
                    new_position = pd.DataFrame([{
                        "Ticker": ticker,
                        "Anteile": order["quantity"],
                        "Einstiegspreis": current_price,
                        "Kaufdatum": datetime.now().strftime("%Y-%m-%d")
                    }])
                    user_portfolio = pd.concat([user_portfolio, new_position], ignore_index=True)
                    user_portfolio.to_csv(f"portfolio_{order['username']}.csv", index=False)
                
                # If this is a sell order, update portfolio
                elif order["order_type"] == "sell":
                    user_portfolio = load_portfolio() if order["username"] == st.session_state["username"] else pd.read_csv(f"portfolio_{order['username']}.csv")
                    ticker_positions = user_portfolio[user_portfolio["Ticker"] == ticker]
                    
                    # Simple implementation - just reduce the first matching position
                    if not ticker_positions.empty:
                        idx = ticker_positions.index[0]
                        if user_portfolio.loc[idx, "Anteile"] > order["quantity"]:
                            user_portfolio.loc[idx, "Anteile"] -= order["quantity"]
                        else:
                            user_portfolio = user_portfolio.drop(idx)
                        
                        user_portfolio.to_csv(f"portfolio_{order['username']}.csv", index=False)
                
                executed_orders.append({
                    "username": order["username"],
                    "ticker": ticker,
                    "type": order["order_type"],
                    "price": current_price,
                    "quantity": order["quantity"]
                })
        except Exception as e:
            st.warning(f"Error processing order for {ticker}: {e}")
    
    # Save updated orders
    df.to_csv(ORDERS_FILE, index=False)
    return executed_orders

def cancel_order(username, index):
    df = load_orders()
    user_orders = df[df["username"] == username]
    if index < len(user_orders):
        order_created_at = user_orders.iloc[index]["created_at"]
        df.loc[(df["username"] == username) & (df["created_at"] == order_created_at), "status"] = "cancelled"
        df.to_csv(ORDERS_FILE, index=False)
        return True
    return False

# Initialize the orders file
init_orders_file()

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

def generate_chatbot_response(client, query, ticker=None):
    """Generate a response to the user's query using the LLM"""
    try:
        if ticker:
            # Get stock information
            stock_data = get_stock_info(ticker)
            context = f"Information about {ticker}:\n{json.dumps(stock_data, indent=2)}\n\n"
        else:
            context = "The user is asking a general stock market question.\n\n"
        
        # Generate response with OpenAI API
        if api_key:
            url = "https://api.deepseek.com/v1/chat/completions"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "deepseek-chat",  # Use the appropriate model name for DeepSeek
                "messages": [
                    {"role": "system", "content": "You are a helpful stock market assistant. Answer questions about stocks, provide financial advice, and help with investment decisions. Keep responses concise and informative."},
                    {"role": "user", "content": f"{context}User question: {query}"}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }

            response = requests.post(url, headers=headers, json=payload)
            
            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"API Error: {response.status_code}. Please check your DeepSeek API key."
            
        else:
            # Fallback response if no API key is provided
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
    df = load_portfolio()

    with st.form("portfolio_form"):
        st.subheader("Neue Position hinzufügen")
        ticker = st.text_input("Ticker (z. B. AAPL)").upper()
        anteile = st.number_input("Anzahl der Anteile", min_value=0.0, value=0.0)
        preis = st.number_input("Einstiegspreis ($)", min_value=0.0, value=0.0)
        kaufdatum = st.date_input("Kaufdatum", value=date.today())
        submitted = st.form_submit_button("Hinzufügen")

        if submitted and ticker:
            new_row = pd.DataFrame([{
                "Ticker": ticker,
                "Anteile": anteile,
                "Einstiegspreis": preis,
                "Kaufdatum": kaufdatum
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            save_portfolio(df)
            st.success(f"{ticker} hinzugefügt!")
            st.rerun()

    st.subheader("📦 Aktuelles Portfolio")
    st.dataframe(df.set_index("Ticker"), use_container_width=True)

# ------------------ Übersicht ------------------
elif page == "Übersicht":
    st.title("📈 Portfolio Übersicht")
    df = load_portfolio()
    if df.empty:
        st.warning("Bitte erfasse zuerst Positionen unter 'Portfolio verwalten'.")
        st.stop()

    tickers = df["Ticker"].tolist()
    benchmarks = {
        "S&P 500": "^GSPC",
        "Nasdaq": "^IXIC",
        "MSCI World": "URTH"
    }
    selected_benchmarks = st.multiselect("🔍 Benchmarks auswählen", options=list(benchmarks.keys()), default=["S&P 500"])
    all_tickers = tickers + [benchmarks[b] for b in selected_benchmarks]

    data = get_price_history(all_tickers)
    if data.empty:
        st.warning("⚠️ Keine Kursdaten gefunden.")
        st.stop()

    latest_prices = data.iloc[-1]
    df["Aktueller Kurs"] = df["Ticker"].map(latest_prices)
    df["Kaufwert"] = df["Anteile"] * df["Einstiegspreis"]
    df["Aktueller Wert"] = df["Anteile"] * df["Aktueller Kurs"]
    df["Gewinn/Verlust €"] = df["Aktueller Wert"] - df["Kaufwert"]
    df["Gewinn/Verlust %"] = (df["Gewinn/Verlust €"] / df["Kaufwert"]) * 100

    total_value = df["Aktueller Wert"].sum()
    total_cost = df["Kaufwert"].sum()

    col1, col2 = st.columns(2)
    col1.metric("📦 Gesamtwert", f"${total_value:,.2f}")
    col2.metric("📈 Performance", f"{((total_value - total_cost)/total_cost)*100:.2f}%", delta=f"${(total_value - total_cost):,.2f}")

    st.subheader("📊 Portfolio Verlauf")

    shares_dict = dict(zip(df["Ticker"], df["Anteile"]))
    portfolio_history = pd.DataFrame(index=data.index)

    # Berechne Portfoliowerte unter Beachtung des Kaufdatums
    for _, row in df.iterrows():
        ticker = row["Ticker"]
        anzahl = row["Anteile"]
        kaufdatum = row["Kaufdatum"]

        if ticker in data.columns:
            werte = data[ticker].copy()
            werte[data.index.tz_localize(None) < pd.to_datetime(kaufdatum)] = 0  # Maskiere vor Kaufdatum
            portfolio_history[ticker] = werte * anzahl

    # Gesamter Portfolio-Wert über Zeit
    portfolio_history["Total"] = portfolio_history.sum(axis=1)

    # Bestimme den ersten investierten Wert
    valid_values = portfolio_history["Total"][portfolio_history["Total"] > 0]
    if not valid_values.empty:
        first_valid_value = valid_values.iloc[0]
    else:
        first_valid_value = 1  # Fallback für leeres Portfolio, um Fehler zu vermeiden

    # Plot mit Plotly
    fig = make_subplots()
    fig.add_trace(go.Scatter(
        x=portfolio_history.index,
        y=portfolio_history["Total"],
        name="Portfolio",
        line=dict(width=3)
    ))

    # Benchmarks normieren und einzeichnen
    for name in selected_benchmarks:
        bm_symbol = benchmarks[name]
        if bm_symbol in data.columns:
            benchmark = data[bm_symbol].copy()
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
    for _, row in df.iterrows():
        if st.button(f"{row['Ticker']} auswählen"):
            st.session_state["selected_ticker"] = row["Ticker"]
            st.rerun()
    st.dataframe(df.set_index("Ticker").round(2), use_container_width=True)

    st.subheader("💸 Dividenden")
    dividend_data = []
    for ticker in tickers:
        divs = get_dividends(ticker)
        if not divs.empty:
            total = divs.sum() * df.loc[df["Ticker"] == ticker, "Anteile"].values[0]
            dividend_data.append((ticker, total, len(divs)))
    if dividend_data:
        div_df = pd.DataFrame(dividend_data, columns=["Ticker", "Summe Dividenden ($)", "Zahlungen"])
        st.dataframe(div_df.set_index("Ticker").round(2))
    else:
        st.info("Keine Dividenden im aktuellen Zeitraum.")

    st.subheader("⚖️ Rebalancing Analyse")
    df["Gewichtung"] = df["Aktueller Wert"] / total_value * 100
    target = 100 / len(df)
    df["Abweichung"] = df["Gewichtung"] - target
    st.dataframe(df[["Ticker", "Aktueller Wert", "Gewichtung", "Abweichung"]].set_index("Ticker").round(2))

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
    col4.metric("Dividende/Aktie", f"${info.get('dividendRate', 0)::.2f}")

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
    current_time = datetime.now().timestamp()
    if current_time - st.session_state["orders_checked"] > 120:
        with st.spinner("Checking pending orders..."):
            executed_orders = check_orders()
            if executed_orders:
                st.success(f"🎉 {len(executed_orders)} order(s) were executed!")
                for order in executed_orders:
                    if order["username"] == st.session_state["username"]:
                        st.info(f"Your {order['type']} order for {order['quantity']} shares of {order['ticker']} was executed at ${order['price']:.2f}!")
        st.session_state["orders_checked"] = current_time
    
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
        
        # Portfolio information
        df = load_portfolio()
        total_holdings = {}
        
        if not df.empty:
            # Group by ticker to show total holdings
            for ticker, group in df.groupby("Ticker"):
                total_holdings[ticker] = group["Anteile"].sum()
            
            # Display current holdings
            st.info("Your current holdings:")
            holdings_text = ", ".join(f"{ticker}: {shares} shares" for ticker, shares in total_holdings.items())
            st.text(holdings_text)
        
        # Form to create new automated orders
        with st.form("order_form"):
            st.subheader("Create New Order")
            
            col1, col2 = st.columns(2)
            with col1:
                ticker = st.text_input("Ticker Symbol (e.g., AAPL)").upper()
                order_type = st.selectbox("Order Type", ["buy", "sell"])
            
            with col2:
                if ticker:
                    try:
                        stock = yf.Ticker(ticker)
                        current_price = stock.info.get("regularMarketPrice", 0)
                        if current_price:
                            st.metric("Current Price", f"${current_price:.2f}")
                            
                            # Set default price based on order type
                            default_price = current_price * 0.95 if order_type == "buy" else current_price * 1.05
                            price = st.number_input("Target Price ($)", 
                                                min_value=0.01, 
                                                value=float(f"{default_price:.2f}"),
                                                help="Order will execute when price reaches this level")
                        else:
                            price = st.number_input("Target Price ($)", min_value=0.01, value=1.00)
                    except:
                        st.warning("Could not fetch current price. Enter target price manually.")
                        price = st.number_input("Target Price ($)", min_value=0.01, value=1.00)
                else:
                    price = st.number_input("Target Price ($)", min_value=0.01, value=1.00)
                
                quantity = st.number_input("Quantity", min_value=0.01, value=1.0)
            
            submitted = st.form_submit_button("Create Order")
            
            if submitted:
                if ticker and price > 0 and quantity > 0:
                    if order_type == "sell":
                        # Check if user has enough shares to sell
                        if ticker in total_holdings and total_holdings[ticker] >= quantity:
                            success = add_order(st.session_state["username"], ticker, order_type, price, quantity)
                            if success:
                                st.success(f"Order created! Will {order_type} {quantity} shares of {ticker} when price reaches ${price:.2f}")
                        else:
                            st.error(f"Not enough shares of {ticker} in your portfolio for this sell order.")
                    else:
                        success = add_order(st.session_state["username"], ticker, order_type, price, quantity)
                        if success:
                            st.success(f"Order created! Will {order_type} {quantity} shares of {ticker} when price reaches ${price:.2f}")
                else:
                    st.error("Please enter a valid ticker, price, and quantity.")
                    
        # Display pending orders
        st.subheader("Your Pending Orders")
        orders_df = load_orders(st.session_state["username"])
        if not orders_df.empty:
            # Filter to show only pending orders
            pending_orders = orders_df[orders_df["status"] == "pending"]
            
            if not pending_orders.empty:
                # Add a cancel button to each order
                for i, order in pending_orders.reset_index().iterrows():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    col1.write(f"{order['ticker']}")
                    col2.write(f"{order['order_type'].capitalize()}")
                    col3.write(f"${order['price']:.2f} × {order['quantity']}")
                    if col4.button(f"Cancel", key=f"cancel_{i}"):
                        if cancel_order(st.session_state["username"], i):
                            st.success(f"Order for {order['ticker']} cancelled")
                            st.rerun()
            else:
                st.info("You have no pending orders.")
        else:
            st.info("You have no pending orders.")
            
        # Display order history (executed and cancelled)
        if not orders_df.empty and "executed" in orders_df["status"].values or "cancelled" in orders_df["status"].values:
            st.subheader("Order History")
            history_orders = orders_df[orders_df["status"].isin(["executed", "cancelled"])]
            if not history_orders.empty:
                for _, order in history_orders.iterrows():
                    status_color = "green" if order["status"] == "executed" else "gray"
                    st.write(f"{order['ticker']} - {order['order_type'].capitalize()} {order['quantity']} shares at ${order['price']:.2f} - "
                             f"<span style='color:{status_color}'>{order['status'].upper()}</span> on {order['created_at']}", unsafe_allow_html=True)

# ------------------ Logout ------------------
st.sidebar.markdown("---")
if st.sidebar.button("🔓 Logout"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["selected_ticker"] = None
    st.rerun()
