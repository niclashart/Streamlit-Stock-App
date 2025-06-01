# User management functions for Streamlit Stock App
import hashlib
import pandas as pd
import os

USER_FILE = "users.csv"


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
    new_user = pd.DataFrame(
        [{"username": username, "password_hash": hash_password(password)}]
    )
    if df.empty:
        df = new_user
    else:
        df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(USER_FILE, index=False)


def validate_login(username, password):
    df = load_users()
    if username in df["username"].values:
        hashed_pw = hash_password(password)
        return (
            hashed_pw == df.loc[df["username"] == username, "password_hash"].values[0]
        )
    return False


def update_password(username, new_password):
    df = load_users()
    if username in df["username"].values:
        df.loc[df["username"] == username, "password_hash"] = hash_password(
            new_password
        )
        df.to_csv(USER_FILE, index=False)
        return True
    return False
