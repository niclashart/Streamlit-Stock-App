import streamlit as st
from src.models.user import UserModel

def login_view():
    """Login view for the application"""
    st.title("🔐 Login / Registrierung")
    mode = st.radio("Modus wählen:", ["Login", "Registrieren", "Passwort vergessen?"])
    username = st.text_input("Benutzername")
    password = st.text_input("Passwort", type="password") if mode != "Passwort vergessen?" else ""

    if mode == "Login":
        if st.button("Einloggen"):
            if username and password:
                if UserModel.validate(username, password):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.rerun()
                else:
                    st.error("Ungültiger Benutzername oder Passwort")
            else:
                st.error("Bitte Benutzername und Passwort eingeben")
    
    elif mode == "Registrieren":
        if st.button("Registrieren"):
            if username and password:
                if UserModel.create(username, password):
                    st.success("Benutzer erfolgreich registriert!")
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.rerun()
                else:
                    st.error("Registrierung fehlgeschlagen. Benutzer könnte bereits existieren.")
            else:
                st.error("Bitte Benutzername und Passwort eingeben")
    
    elif mode == "Passwort vergessen?":
        new_pass = st.text_input("Neues Passwort", type="password")
        if st.button("Zurücksetzen"):
            if username and new_pass:
                if UserModel.update_password(username, new_pass):
                    st.success("Passwort erfolgreich zurückgesetzt!")
                else:
                    st.error("Passwort-Zurücksetzung fehlgeschlagen. Benutzer existiert nicht.")
            else:
                st.error("Bitte Benutzername und neues Passwort eingeben")
