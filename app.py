import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Drinking Water Access Dashboard", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join(BASE_DIR, "API_SH.H2O.SMDW.ZS_DS2_en_csv_v2_3203.csv"), skiprows=4)
    meta = pd.read_csv(os.path.join(BASE_DIR, "Metadata_Country_API_SH.H2O.SMDW.ZS_DS2_en_csv_v2_3203.csv"))
