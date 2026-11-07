import streamlit as st

def show_landing_page():
    # Buang ruang kosong atas, tolak paparan naik ke atas
    st.markdown("""
        <style>
            .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem;
            }
            h1 {
                margin-top: 0rem;
                padding-top: 0rem;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #2563EB; margin-top: 0px;'>Landing Page</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Selamat datang ke sistem kami.</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Tekan butang di bawah untuk masuk.</p>", unsafe_allow_html=True)

    # CONTOH - Untuk nampak mana col1, col2, col3
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown("<p style='text-align: center; color: red;'><b>INI COL1<br>KIRI</b></p>", unsafe_allow_html=True)
    with col2:
        st.markdown("<p style='text-align: center; color: green;'><b>INI COL2<br>TENGAH</b></p>", unsafe_allow_html=True)
    with col3:
        st.markdown("<p style='text-align: center; color: orange;'><b>INI COL3<br>KANAN</b></p>", unsafe_allow_html=True)

    st.markdown("---")

    # Butang Masuk - kekal kat tengah guna col2
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1, col2, col3:
        if st.button("Masuk", use_container_width=True):
            st.session_state.masuk = True
            st.rerun()
