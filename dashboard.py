import streamlit as st
import json
import os

DATA_FILE = "analytics_data.json"

st.set_page_config(page_title="Buddy Dashboard", layout="wide")

st.title("🤖 Buddy AI Real-Time Dashboard")

if not os.path.exists(DATA_FILE):
    st.warning("Run Buddy once to generate analytics file.")
else:
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Commands", data["total_commands"])
    col2.metric("Files Created", data["files_created"])
    col3.metric("Websites Opened", data["websites_opened"])
    col4.metric("Volume Actions", data["volume_actions"])
    col5.metric("Errors", data["errors"])

    st.subheader("Recent Activity")
    st.write(data["history"][-10:])
