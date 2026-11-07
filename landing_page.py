import streamlit as st

def show_landing_page():
    st.title("SISTEM BERKAT USAHA PASTI BERJAYA")
    st.write("Selamat datang ke sistem kami.")
    st.write("Tekan butang di bawah untuk masuk.")

    if st.button("Masuk"):
        st.session_state.masuk = True
        st.rerun()
