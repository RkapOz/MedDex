# med_pokedex_app.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- Setup DB ---
conn = sqlite3.connect('patients.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                gender TEXT,
                birth_date TEXT,
                visit_date TEXT,
                UNIQUE(name, birth_date))''')
conn.commit()

# --- Authentication ---
def login():
    st.title("MedPokeDex - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        user = c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        if user:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
        else:
            st.error("Invalid credentials")

def register():
    with st.expander("Register"):
        username = st.text_input("New Username")
        password = st.text_input("New Password", type='password')
        if st.button("Create Account"):
            try:
                c.execute("INSERT INTO users VALUES (?, ?)", (username, password))
                conn.commit()
                st.success("Account created. Please login.")
            except:
                st.error("Username already exists.")

# --- Patient Form ---
def add_patient():
    st.title("Add Patient")
    name = st.text_input("Full Name")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    birth_date = st.date_input("Birth Date")
    visit_date = st.date_input("Visit Date", value=datetime.today())
    if st.button("Save Record"):
        try:
            c.execute("INSERT INTO patients (name, gender, birth_date, visit_date) VALUES (?, ?, ?, ?)",
                      (name, gender, birth_date.isoformat(), visit_date.isoformat()))
            conn.commit()
            st.success("Patient record saved.")
        except sqlite3.IntegrityError:
            st.warning("Duplicate entry: This patient already exists.")

# --- Dashboard ---
def show_dashboard():
    st.title("Patient Dashboard")
    df = pd.read_sql_query("SELECT * FROM patients", conn)
    if df.empty:
        st.info("No patient data yet.")
        return

    df['visit_date'] = pd.to_datetime(df['visit_date'])
    df['month'] = df['visit_date'].dt.to_period('M')

    st.subheader("Patient Gender Distribution")
    st.bar_chart(df['gender'].value_counts())

    st.subheader("Patients This Month")
    top_month = df['month'].value_counts().idxmax()
    st.write(f"Most patients came in: **{top_month}**")

    st.subheader("Export Patient Count by Month")
    count_df = df.groupby('month').size().reset_index(name='patient_count')
    st.dataframe(count_df)
    csv = count_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Monthly Count CSV", data=csv, file_name='monthly_patient_count.csv', mime='text/csv')

# --- Main App ---
def main():
    if 'logged_in' not in st.session_state:
        login()
        register()
    else:
        menu = st.sidebar.radio("Menu", ["Add Patient", "Dashboard", "Logout"])
        if menu == "Add Patient":
            add_patient()
        elif menu == "Dashboard":
            show_dashboard()
        elif menu == "Logout":
          for key in list(st.session_state.keys()):
            del st.session_state[key]
          st.success("You have been logged out. Please refresh the page.")
          st.experimental_rerun()

if __name__ == '__main__':
    main()
