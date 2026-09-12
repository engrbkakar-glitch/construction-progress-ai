import streamlit as st
import pandas as pd
from pathlib import Path
from PIL import Image

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Construction Progress Monitor",
    page_icon="🏗️",
    layout="wide",
)

# ============================================================
# FILE PATHS
# ============================================================
BASE_DIR = Path(__file__).parent
BOQ_PATH = BASE_DIR / "data" / "boq.csv"
PROGRESS_PATH = BASE_DIR / "data" / "progress.csv"

# ============================================================
# LOAD DATA
# ============================================================
try:
    boq = pd.read_csv(BOQ_PATH)
    progress = pd.read_csv(PROGRESS_PATH)
except FileNotFoundError as e:
    st.error("Required data file was not found.")
    st.write(f"Check that these files exist: {BOQ_PATH} and {PROGRESS_PATH}")
    st.stop()

# Convert numeric columns
for col in ["boq_quantity", "rate", "boq_amount", "weight"]:
    boq[col] = pd.to_numeric(boq[col], errors="coerce").fillna(0)

for col in ["physical_progress", "financial_progress"]:
    progress[col] = (
        pd.to_numeric(progress[col], errors="coerce")
        .fillna(0)
        .clip(0, 100)
    )

# Combine BOQ and progress
data = boq.merge(progress, on="item_id", how="left")

data["physical_progress"] = data["physical_progress"].fillna(0)
data["financial_progress"] = data["financial_progress"].fillna(0)

# Activity-level variance
data["variance"] = (
    data["physical_progress"] - data["financial_progress"]
)

# ============================================================
# CALCULATIONS
# ============================================================
contract_amount = float(data["boq_amount"].sum())
total_weight = float(data["weight"].sum())

if total_weight > 0:
    physical_progress = float(
        (data["physical_progress"] * data["weight"] / total_weight).sum()
    )

    financial_progress = float(
        (data["financial_progress"] * data["weight"] / total_weight).sum()
    )
else:
    physical_progress = 0.0
    financial_progress = 0.0

variance = physical_progress - financial_progress

physical_value = contract_amount * physical_progress / 100
financial_value = contract_amount * financial_progress / 100

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.header("🏗️ Project Information")

project_name = st.sidebar.text_input(
    "Project Name",
    "Small Construction Project",
)

project_type = st.sidebar.selectbox(
    "Project Type",
    [
        "Road Construction",
        "Building Construction",
        "Drainage Project",
        "Other",
    ],
)

# ============================================================
# HEADER
# ============================================================
st.title("🏗️ Construction Progress Monitor")

st.subheader(
    "AI-assisted Physical vs Financial Progress Monitoring System"
)

st.write(
    "Construction BOQ, financial progress and site evidence "
    "are brought together to support project monitoring."
)

# ============================================================
# PROJECT OVERVIEW
# ============================================================
st.divider()
st.subheader("Project Overview")

st.write(f"**Project:** {project_name}")
st.write(f"**Project Type:** {project_type}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Contract Amount",
        f"PKR {contract_amount / 1_000_000:.2f} M",
    )

with col2:
    st.metric(
        "Physical Progress",
        f"{physical_progress:.2f}%",
    )

with col3:
    st.metric(
        "Financial Progress",
        f"{financial_progress:.2f}%",
    )

with col4:
    st.metric(
        "Variance",
        f"{variance:+.2f} pp",
    )

# ============================================================
# VARIANCE MESSAGE
# ============================================================
if variance < -10:
    st.error(
        f"🔴 Financial progress is significantly ahead of physical "
        f"progress by {abs(variance):.2f} percentage points."
    )
elif variance < 0:
    st.warning(
        f"🟡 Financial progress is ahead of physical progress by "
        f"{abs(variance):.2f} percentage points."
    )
elif variance > 10:
    st.warning(
        f"🟠 Physical progress is significantly ahead of financial "
        f"progress by {variance:.2f} percentage points."
    )
elif variance > 0:
    st.info(
        f"🔵 Physical progress is ahead of financial progress by "
        f"{variance:.2f} percentage points."
    )
else:
    st.success(
        "🟢 Physical and financial progress are aligned."
    )

# ============================================================
# PROGRESS CHART
# Uses Streamlit's built-in chart, so Plotly is NOT required.
# ============================================================
st.divider()
st.subheader("📈 Physical vs Financial Progress")

chart_data = data[
    ["activity", "physical_progress", "financial_progress"]
].copy()

chart_data = chart_data.set_index("activity")

st.bar_chart(
    chart_data,
    y=["physical_progress", "financial_progress"],
)

# ============================================================
# ACTIVITY TABLE
# ============================================================
st.subheader("📊 Activity-Level Progress")

display_data = data[
    [
        "item_id",
        "activity",
        "unit",
        "weight",
        "physical_progress",
        "financial_progress",
        "variance",
    ]
].copy()

display_data.columns = [
    "ID",
    "Activity",
    "Unit",
    "Weight (%)",
    "Physical (%)",
    "Financial (%)",
    "Variance (pp)",
]

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True,
)

# ============================================================
# PROGRESS VALUE
# ============================================================
st.subheader("💰 Progress Value")

v1, v2, v3 = st.columns(3)

with v1:
    st.metric(
        "Contract Value",
        f"PKR {contract_amount:,.0f}",
    )

with v2:
    st.metric(
        "Physical Progress Value",
        f"PKR {physical_value:,.0f}",
    )

with v3:
    st.metric(
        "Financial Progress Value",
        f"PKR {financial_value:,.0f}",
    )

# ============================================================
# BOQ
# ============================================================
with st.expander("📋 View Project BOQ"):
    st.dataframe(
        boq,
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# SITE IMAGE UPLOAD
# ============================================================
st.divider()
st.subheader("📷 Site Evidence")

st.write(
    "Upload a construction site photograph. AI image analysis "
    "will be connected after the core dashboard is stable."
)

uploaded_file = st.file_uploader(
    "Upload Site Image",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
    image = Image.open(uploaded_file)

    st.image(
        image,
        caption="Uploaded Construction Site Evidence",
        use_container_width=True,
    )

    st.info(
        "Image uploaded successfully. The next development stage "
        "will analyze this image using Gemini and compare the "
        "AI estimate with engineer-verified progress."
    )

# ============================================================
# ENGINEER VERIFICATION
# ============================================================
st.divider()
st.subheader("👷 Engineer Verification")

selected_activity = st.selectbox(
    "Select Activity",
    data["activity"].tolist(),
)

selected_row = data[
    data["activity"] == selected_activity
].iloc[0]

ai_estimate = st.number_input(
    "AI Visual Estimate (%)",
    min_value=0.0,
    max_value=100.0,
    value=float(selected_row["physical_progress"]),
    step=1.0,
)

verified_progress = st.number_input(
    "Engineer Verified Progress (%)",
    min_value=0.0,
    max_value=100.0,
    value=float(selected_row["physical_progress"]),
    step=1.0,
)

engineer_notes = st.text_area(
    "Engineer Remarks",
    placeholder=(
        "Example: Visual evidence supports ongoing work. "
        "Final quantity requires measurement record."
    ),
)

if st.button("✅ Record Verification"):
    st.success(
        f"{selected_activity}: engineer verified progress is "
        f"{verified_progress:.1f}%."
    )
    st.caption(
        "Prototype: verification is currently displayed for the "
        "current session and is not permanently stored."
    )

# ============================================================
# INTERPRETATION
# ============================================================
st.divider()
st.subheader("🧠 Project Monitoring Interpretation")

if variance < -10:
    interpretation = (
        "Financial progress is substantially ahead of physical "
        "progress. Review measurements, payment records and "
        "supporting financial documentation."
    )
elif variance < 0:
    interpretation = (
        "Financial progress is ahead of physical progress. "
        "Review the relevant measurements and financial records "
        "in the context of the project."
    )
elif variance > 10:
    interpretation = (
        "Physical progress is substantially ahead of financial "
        "progress. Review whether financial reporting or claims "
        "are lagging behind completed work."
    )
elif variance > 0:
    interpretation = (
        "Physical progress is ahead of financial progress. "
        "Review whether financial reporting or claims are "
        "lagging behind completed work."
    )
else:
    interpretation = (
        "Physical and financial progress are aligned."
    )

st.write(interpretation)

st.caption(
    "Important: AI image analysis is supporting evidence. Final "
    "physical progress should be based on engineer-verified "
    "quantities, measurements and BOQ weights."
)
