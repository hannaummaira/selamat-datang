# -*- coding: utf-8 -*-
"""Sistem Pelantikan Petugas SPM Selangor 2026 - SATU URL (JPN + 10 PPD). Main file: app.py"""
import streamlit as st
import os
try:
    _P = str(st.secrets.get("PROGRAM", os.environ.get("PROGRAM", "SPM"))).strip().upper()
except Exception:
    _P = os.environ.get("PROGRAM", "SPM").strip().upper()
_P = _P if _P in ("UBBM", "UBBI") else "SPM"
st.set_page_config(page_title=f"{_P} 2026 - Selangor", layout="wide", page_icon="📚", initial_sidebar_state="collapsed")
from main_app import run_app
run_app()
