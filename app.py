import streamlit as st
import pandas as pd

boq = pd.read_csv("data/boq.csv")
progress = pd.read_csv("data/progress.csv")

data = boq.merge(progress, on="item_id")

data["variance"] = (
    data["physical_progress"] - data["financial_progress"]
)

physical_progress = (
    data["physical_progress"] * data["weight"] / 100
).sum()

financial_progress = (
    data["financial_progress"] * data["weight"] / 100
).sum()

variance = physical_progress - financial_progress

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
        f"⚠️ Financial progress is significantly ahead "
        f"of physical progress by {abs(variance):.2f} percentage points."
    )

elif variance < 0:
    st.warning(
        f"⚠️ Financial progress is ahead of physical progress "
        f"by {abs(variance):.2f} percentage points."
    )

elif variance > 10:
    st.warning(
        f"⚠️ Physical progress is significantly ahead "
        f"of financial progress by {variance:.2f} percentage points."
    )

elif variance > 0:
    st.info(
        f"ℹ️ Physical progress is ahead of financial progress "
        f"by {variance:.2f} percentage points."
    )

else:
    st.success(
        "✅ Physical and financial progress are aligned."
    )
st.divider()

st.subheader("📋 Project BOQ")

st.dataframe(
    boq,
    use_container_width=True,
    hide_index=True
)
st.divider()

st.subheader("📊 Activity-Level Progress")

st.dataframe(
    data[
        [
            "item_id",
            "activity",
            "weight",
            "physical_progress",
            "financial_progress",
            "variance"
        ]
    ],
    use_container_width=True,
    hide_index=True
)
