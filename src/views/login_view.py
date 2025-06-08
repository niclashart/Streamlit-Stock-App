"""
Login view module for handling authentication and registration UI
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from models.user import UserService

def show_login_view() -> None:
    """
    Display the login/registration view
    Returns True if login is successful, False otherwise
    """
    st.title("🔐 Login / Registrierung")
    user_service = UserService()
    
    # Create a radio button for login mode selection
    mode = st.radio("Modus wählen:", ["Login", "Registrieren", "Passwort vergessen?"])
    username = st.text_input("Benutzername")
    
    if mode == "Login":
        password = st.text_input("Passwort", type="password")
        if st.button("Einloggen"):
            if user_service.login(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Willkommen zurück, {username}!")
                st.rerun()
            else:
                st.error("❌ Falscher Benutzername oder Passwort.")
                
    elif mode == "Registrieren":
        password = st.text_input("Passwort", type="password")
        if st.button("Registrieren"):
            if username == "" or password == "":
                st.warning("Bitte Benutzername und Passwort eingeben.")
            else:
                if user_service.register(username, password):
                    st.success("Registrierung erfolgreich. Du kannst dich nun einloggen.")
                else:
                    st.warning("Benutzername bereits vergeben.")
                    
    elif mode == "Passwort vergessen?":
        new_pass = st.text_input("Neues Passwort", type="password")
        if st.button("Zurücksetzen"):
            if user_service.update_password(username, new_pass):
                st.success("Passwort wurde aktualisiert. Du kannst dich jetzt einloggen.")
            else:
                st.error("Benutzername nicht gefunden.")
    
    # Stop execution if not logged in
    if not st.session_state.get("logged_in", False):
        st.stop()
