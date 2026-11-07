import streamlit as st
from landing_page import show_landing_page

st.set_page_config(page_title="Selamat Datang", layout="centered")

# Simpan status dah masuk ke belum
if "masuk" not in st.session_state:
    st.session_state.masuk = False

# Kalau belum masuk, tunjuk landing page
if not st.session_state.masuk:
    show_landing_page()
else:
    st.title("Selamat Datang")
    if st.button("Kembali ke Landing Page"):
        st.session_state.masuk = False
        st.rerun()
