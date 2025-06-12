"""
Streamlit Stock App - Main Application
A modular stock portfolio tracking and analysis application

Author: Niclas
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from controllers.app_controller import AppController
from services.trading_bot_service import trading_bot

# Configure the page
st.set_page_config(
    page_title="Stock Portfolio App",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Run the application
if __name__ == "__main__":
    # Start the trading bot service in the background
    trading_bot.start()
    
    # Run the main application
    controller = AppController()
    controller.run()
