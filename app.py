import hashlib
import pandas as pd
import streamlit as st
import os
import yfinance as yf
from datetime import date
import plotly.graph_objects as go
from plotly.subplots import make_subplots

USER_FILE = "users.csv"

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
page = st.sidebar.radio("Seite auswählen", ["Übersicht", "Portfolio verwalten", "📄 Einzelanalyse"])

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
    col4.metric("Dividende/Aktie", f"${info.get('dividendRate', 0):.2f}")

    st.subheader("📈 Kursverlauf (6 Monate)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], name="Close"))
    fig.update_layout(xaxis_title="Datum", yaxis_title="Preis ($)")
    st.plotly_chart(fig, use_container_width=True)

# ------------------ Logout ------------------
st.sidebar.markdown("---")
if st.sidebar.button("🔓 Logout"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["selected_ticker"] = None
    st.rerun()
