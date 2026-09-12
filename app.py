import streamlit as st
import pandas as pd

boq = pd.read_csv("data/boq.csv")
# Page configuration
st.set_page_config(
    page_title="Construction Progress Monitor",
    page_icon="🏗️",
    layout="wide"
)

# Title
st.title("🏗️ Construction Progress Monitor")

st.write(
    "AI-assisted Physical vs Financial "
    "Progress Monitoring System"
)

st.divider()

# Project information
st.subheader("Project Overview")

project_name = "Small Construction Project"
contract_amount = 4500000

# Demo progress
physical_progress = 48
financial_progress = 62

variance = physical_progress - financial_progress

# Display project
st.write(f"**Project:** {project_name}")

# Four columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Contract Amount",
        "PKR 4.50 M"
    )

with col2:
    st.metric(
        "Physical Progress",
        f"{physical_progress}%"
    )

with col3:
    st.metric(
        "Financial Progress",
        f"{financial_progress}%"
    )

with col4:
    st.metric(
        "Variance",
        f"{variance:+}%"
    )

# Warning
if variance < -10:
    st.error(
        "⚠️ Financial progress is significantly "
        "ahead of physical progress."
    )
else:
    st.success(
        "✅ Physical and financial progress "
        "are relatively aligned."
    )
st.divider()

st.subheader("📋 Project BOQ")

st.dataframe(
    boq,
    use_container_width=True,
    hide_index=True
)
