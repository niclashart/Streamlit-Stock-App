"""
Main application controller to manage navigation and application flow
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from views.login_view import show_login_view
from views.overview_view import show_overview_view
from views.portfolio_management_view import show_portfolio_management_view
from views.analysis_view import show_analysis_view
from views.trading_bot_view import show_trading_bot_view

class AppController:
    """Main application controller class"""
    
    PAGES = {
        "Übersicht": show_overview_view,
        "Portfolio verwalten": show_portfolio_management_view,
        "📄 Einzelanalyse": show_analysis_view,
        "🤖 Buy Bot": show_trading_bot_view
    }
    
    def __init__(self):
        """Initialize controller and setup session state"""
        # Initialize session state variables
        if "logged_in" not in st.session_state:
            st.session_state["logged_in"] = False
            
        if "username" not in st.session_state:
            st.session_state["username"] = ""
            
        if "selected_ticker" not in st.session_state:
            st.session_state["selected_ticker"] = None
            
    def setup_sidebar(self):
        """Setup sidebar navigation"""
        st.sidebar.title("📂 Navigation")
        selected_page = st.sidebar.radio("Seite auswählen", list(self.PAGES.keys()))
        
        # Add logout button
        st.sidebar.markdown("---")
        if st.sidebar.button("🔓 Logout"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["selected_ticker"] = None
            st.rerun()
            
        return selected_page
    
    def run(self):
        """Run the application"""
        # If not logged in, show login page
        if not st.session_state["logged_in"]:
            show_login_view()
            # If login was successful, the session state will be updated
            # and the function will return control
            
        # Show navigation sidebar and get selected page
        selected_page = self.setup_sidebar()
        
        # Display the selected page
        page_function = self.PAGES.get(selected_page)
        if page_function:
            page_function()
