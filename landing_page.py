import streamlit as st

def show_landing_page():
    st.markdown("<h1 style='text-align:center:'>"SISTEM BERKAT USAHA PASTI BERJAYA,layout,/h1",unsafe_allow_html=True)
    st.write("Selamat datang ke sistem kami.")
    st.write("Tekan butang di bawah untuk masuk.")

    if st.button("Masuk"):
        st.session_state.masuk = True
        st.rerun()
