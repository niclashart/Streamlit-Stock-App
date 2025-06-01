import streamlit as st
from datetime import date, datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from user_management import (
    init_user_file,
    load_users,
    save_user,
    validate_login,
    update_password,
)
from portfolio import load_portfolio, save_portfolio, get_price_history, get_dividends
from orders import init_orders_file, load_orders, add_order, check_orders, cancel_order
from stock_api import get_stock_info, generate_chatbot_response
import os
import pandas as pd
import yfinance as yf
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")


# ------------------ Login / Registrierung ------------------
init_user_file()
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""

if not st.session_state["logged_in"]:
    st.title("🔐 Login / Registrierung")
    mode = st.radio("Modus wählen:", ["Login", "Registrieren", "Passwort vergessen?"])
    username = st.text_input("Benutzername")
    password = (
        st.text_input("Passwort", type="password")
        if mode != "Passwort vergessen?"
        else ""
    )

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
                open(f"portfolio_{username}.csv", "w").write(
                    "Ticker,Anteile,Einstiegspreis,Kaufdatum\n"
                )
                st.success("Registrierung erfolgreich. Du kannst dich nun einloggen.")
    elif mode == "Passwort vergessen?":
        new_pass = st.text_input("Neues Passwort", type="password")
        if st.button("Zurücksetzen"):
            if update_password(username, new_pass):
                st.success(
                    "Passwort wurde aktualisiert. Du kannst dich jetzt einloggen."
                )
            else:
                st.error("Benutzername nicht gefunden.")
    st.stop()

# ------------------ Navigation ------------------
st.sidebar.title("📂 Navigation")
page = st.sidebar.radio(
    "Seite auswählen",
    ["Übersicht", "Portfolio verwalten", "📄 Einzelanalyse", "🤖 Buy Bot"],
)

# ------------------ Globale Funktionen ------------------

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
            new_row = pd.DataFrame(
                [
                    {
                        "Ticker": ticker,
                        "Anteile": anteile,
                        "Einstiegspreis": preis,
                        "Kaufdatum": kaufdatum,
                    }
                ]
            )
            if df.empty:
                df = new_row
            else:
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
    benchmarks = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC", "MSCI World": "URTH"}
    selected_benchmarks = st.multiselect(
        "🔍 Benchmarks auswählen", options=list(benchmarks.keys()), default=["S&P 500"]
    )
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
    col2.metric(
        "📈 Performance",
        f"{((total_value - total_cost)/total_cost)*100:.2f}%",
        delta=f"${(total_value - total_cost):,.2f}",
    )

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
            werte[data.index.tz_localize(None) < pd.to_datetime(kaufdatum)] = (
                0  # Maskiere vor Kaufdatum
            )
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
    fig.add_trace(
        go.Scatter(
            x=portfolio_history.index,
            y=portfolio_history["Total"],
            name="Portfolio",
            line=dict(width=3),
        )
    )

    # Benchmarks normieren und einzeichnen
    for name in selected_benchmarks:
        bm_symbol = benchmarks[name]
        if bm_symbol in data.columns:
            benchmark = data[bm_symbol].copy()
            benchmark = benchmark / benchmark.iloc[0] * first_valid_value
            fig.add_trace(
                go.Scatter(
                    x=benchmark.index, y=benchmark, name=name, line=dict(dash="dot")
                )
            )

    fig.update_layout(
        title="Wertentwicklung",
        xaxis_title="Datum",
        yaxis_title="Wert in $",
        height=500,
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
        div_df = pd.DataFrame(
            dividend_data, columns=["Ticker", "Summe Dividenden ($)", "Zahlungen"]
        )
        st.dataframe(div_df.set_index("Ticker").round(2))
    else:
        st.info("Keine Dividenden im aktuellen Zeitraum.")

    st.subheader("⚖️ Rebalancing Analyse")
    df["Gewichtung"] = df["Aktueller Wert"] / total_value * 100
    target = 100 / len(df)
    df["Abweichung"] = df["Gewichtung"] - target
    st.dataframe(
        df[["Ticker", "Aktueller Wert", "Gewichtung", "Abweichung"]]
        .set_index("Ticker")
        .round(2)
    )

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
    col2.metric(
        "Tagesveränderung", f"${hist['Close'].iloc[-1] - hist['Open'].iloc[-1]:.2f}"
    )

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
        st.session_state["orders_checked"] = (
            datetime.now().timestamp() - 120
        )  # Check immediately first time

    # Check for orders that need to be executed (every 2 minutes)
    current_time = datetime.now().timestamp()
    if current_time - st.session_state["orders_checked"] > 120:
        with st.spinner("Checking pending orders..."):
            executed_orders = check_orders()
            if executed_orders:
                st.success(f"🎉 {len(executed_orders)} order(s) were executed!")
                for order in executed_orders:
                    if order["username"] == st.session_state["username"]:
                        st.info(
                            f"Your {order['type']} order for {order['quantity']} shares of {order['ticker']} was executed at ${order['price']:.2f}!"
                        )
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
            st.warning(
                "DeepSeek API key not found. Please add it to your .env file to enable advanced features."
            )
            st.info(
                "Set DEEPSEEK_API_KEY=your_api_key in a .env file in the app directory."
            )

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
                if (
                    token.isalpha()
                    and len(token) <= 5
                    and token
                    not in ["A", "I", "THE", "AND", "OR", "FOR", "WHAT", "HOW", "WHY"]
                ):
                    try:
                        stock = yf.Ticker(token)
                        info = stock.info
                        if "regularMarketPrice" in info:
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
            st.session_state["messages"].append(
                {"role": "assistant", "content": response}
            )

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
            holdings_text = ", ".join(
                f"{ticker}: {shares} shares"
                for ticker, shares in total_holdings.items()
            )
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
                            default_price = (
                                current_price * 0.95
                                if order_type == "buy"
                                else current_price * 1.05
                            )
                            price = st.number_input(
                                "Target Price ($)",
                                min_value=0.01,
                                value=float(f"{default_price:.2f}"),
                                help="Order will execute when price reaches this level",
                            )
                        else:
                            price = st.number_input(
                                "Target Price ($)", min_value=0.01, value=1.00
                            )
                    except:
                        st.warning(
                            "Could not fetch current price. Enter target price manually."
                        )
                        price = st.number_input(
                            "Target Price ($)", min_value=0.01, value=1.00
                        )
                else:
                    price = st.number_input(
                        "Target Price ($)", min_value=0.01, value=1.00
                    )

                quantity = st.number_input("Quantity", min_value=0.01, value=1.0)

            submitted = st.form_submit_button("Create Order")

            if submitted:
                if ticker and price > 0 and quantity > 0:
                    if order_type == "sell":
                        # Check if user has enough shares to sell
                        if (
                            ticker in total_holdings
                            and total_holdings[ticker] >= quantity
                        ):
                            success = add_order(
                                st.session_state["username"],
                                ticker,
                                order_type,
                                price,
                                quantity,
                            )
                            if success:
                                st.success(
                                    f"Order created! Will {order_type} {quantity} shares of {ticker} when price reaches ${price:.2f}"
                                )
                        else:
                            st.error(
                                f"Not enough shares of {ticker} in your portfolio for this sell order."
                            )
                    else:
                        success = add_order(
                            st.session_state["username"],
                            ticker,
                            order_type,
                            price,
                            quantity,
                        )
                        if success:
                            st.success(
                                f"Order created! Will {order_type} {quantity} shares of {ticker} when price reaches ${price:.2f}"
                            )
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
        if (
            not orders_df.empty
            and "executed" in orders_df["status"].values
            or "cancelled" in orders_df["status"].values
        ):
            st.subheader("Order History")
            history_orders = orders_df[
                orders_df["status"].isin(["executed", "cancelled"])
            ]
            if not history_orders.empty:
                for _, order in history_orders.iterrows():
                    status_color = "green" if order["status"] == "executed" else "gray"
                    st.write(
                        f"{order['ticker']} - {order['order_type'].capitalize()} {order['quantity']} shares at ${order['price']:.2f} - "
                        f"<span style='color:{status_color}'>{order['status'].upper()}</span> on {order['created_at']}",
                        unsafe_allow_html=True,
                    )

# ------------------ Logout ------------------
st.sidebar.markdown("---")
if st.sidebar.button("🔓 Logout"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["selected_ticker"] = None
    st.rerun()
