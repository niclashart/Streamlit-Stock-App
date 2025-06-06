import streamlit as st
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime
from plotly.subplots import make_subplots
from dotenv import load_dotenv
import time

# Importieren der Module
from src.database.db import init_db, migrate_data_from_csv
from src.views.login_view import login_view
from src.views.overview_view import overview_view
from src.views.portfolio_view import portfolio_management_view
from src.views.analysis_view import stock_analysis_view
from src.views.buybot_view import buybot_view
from src.utils.common import display_info, display_error, display_success

# Laden der Umgebungsvariablen
load_dotenv()

# Seitenkonfiguration
st.set_page_config(
    page_title="Stock Portfolio App",
    page_icon="📈",
    layout="wide"
)

# Eigenes CSS für bessere Darstellung
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .stProgress .st-bo {
        background-color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Initialisierung der Datenbank mit Fehlerbehandlung
if "db_initialized" not in st.session_state:
    with st.spinner("Initialisiere Datenbank..."):
        db_success = init_db()
        if db_success:
            # Daten von CSV-Dateien migrieren (bei Bedarf)
            migrate_data_from_csv()
            st.session_state["db_initialized"] = True
        else:
            display_error("Datenbankverbindung konnte nicht hergestellt werden. Bitte überprüfe die Verbindungseinstellungen.")
            time.sleep(3)
            st.experimental_rerun()

# Initialisierung des Session States
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""

if "selected_ticker" not in st.session_state:
    st.session_state["selected_ticker"] = None

# Login / Registrierung
if not st.session_state["logged_in"]:
    login_view()
    # Nach dem Login-Versuch stoppen
    st.stop()

# Hauptnavigation
st.sidebar.title("📂 Navigation")
page = st.sidebar.radio("Seite auswählen", ["Übersicht", "Portfolio verwalten", "📄 Einzelanalyse", "🤖 Buy Bot"])

# Seiten-Routing
if page == "Übersicht":
    overview_view(st.session_state["username"])
    
elif page == "Portfolio verwalten":
    portfolio_management_view(st.session_state["username"])
    
elif page == "📄 Einzelanalyse":
    stock_analysis_view(st.session_state.get("selected_ticker"))
    
elif page == "🤖 Buy Bot":
    buybot_view(st.session_state["username"])

# Logout-Button
st.sidebar.markdown("---")
if st.sidebar.button("🔓 Logout"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["selected_ticker"] = None
    st.rerun()
