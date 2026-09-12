import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from PIL import Image

# Optional Gemini support
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

st.set_page_config(
    page_title="Construction Progress Monitor",
    page_icon="🏗️",
    layout="wide",
)

BASE_DIR = Path(__file__).parent
BOQ_PATH = BASE_DIR / "data" / "boq.csv"
PROGRESS_PATH = BASE_DIR / "data" / "progress.csv"

DEMO_BOQ = pd.DataFrame(
    [
        ["E01", "Earthwork", "m3", 1000, 500, 500000, 20],
        ["S01", "Sub-base", "m3", 500, 1500, 750000, 15],
        ["B01", "Base Course", "m3", 400, 2500, 1000000, 20],
        ["A01", "Asphalt", "ton", 100, 17500, 1750000, 35],
        ["D01", "Drainage", "m", 500, 1000, 500000, 10],
    ],
    columns=[
        "item_id", "activity", "unit", "boq_quantity",
        "rate", "boq_amount", "weight"
    ],
)

DEMO_PROGRESS = pd.DataFrame(
    [
        ["E01", 80, 75],
        ["S01", 60, 65],
        ["B01", 45, 50],
        ["A01", 20, 30],
        ["D01", 70, 65],
    ],
    columns=["item_id", "physical_progress", "financial_progress"],
)


def load_data():
    boq = pd.read_csv(BOQ_PATH) if BOQ_PATH.exists() else DEMO_BOQ.copy()
    progress = (
        pd.read_csv(PROGRESS_PATH)
        if PROGRESS_PATH.exists()
        else DEMO_PROGRESS.copy()
    )

    required_boq = {
        "item_id", "activity", "unit", "boq_quantity",
        "rate", "boq_amount", "weight"
    }
    required_progress = {
        "item_id", "physical_progress", "financial_progress"
    }

    missing_boq = required_boq - set(boq.columns)
    missing_progress = required_progress - set(progress.columns)

    if missing_boq:
        st.error("BOQ is missing columns: " + ", ".join(sorted(missing_boq)))
        st.stop()

    if missing_progress:
        st.error(
            "Progress file is missing columns: "
            + ", ".join(sorted(missing_progress))
        )
        st.stop()

    for col in ["boq_quantity", "rate", "boq_amount", "weight"]:
        boq[col] = pd.to_numeric(boq[col], errors="coerce").fillna(0)

    for col in ["physical_progress", "financial_progress"]:
        progress[col] = (
            pd.to_numeric(progress[col], errors="coerce")
            .fillna(0)
            .clip(0, 100)
        )

    data = boq.merge(progress, on="item_id", how="left")
    data["physical_progress"] = data["physical_progress"].fillna(0)
    data["financial_progress"] = data["financial_progress"].fillna(0)
    data["variance"] = (
        data["physical_progress"] - data["financial_progress"]
    )

    return boq, data


boq, data = load_data()

# Sidebar
st.sidebar.header("🏗️ Project Information")

project_name = st.sidebar.text_input(
    "Project Name",
    "Small Construction Project",
)

project_type = st.sidebar.selectbox(
    "Project Type",
    ["Road Construction", "Building Construction", "Drainage Project", "Other"],
)

# Weighted progress
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

# Header
st.title("🏗️ Construction Progress Monitor")
st.write("AI-assisted Physical vs Financial Progress Monitoring System")
st.caption(
    "BOQ + financial data + site evidence → verified physical progress "
    "→ variance analysis"
)

# Overview
st.subheader("Project Overview")
st.write(f"**Project:** {project_name}")
st.write(f"**Type:** {project_type}")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Contract Amount", f"PKR {contract_amount / 1_000_000:.2f} M")
with c2:
    st.metric("Physical Progress", f"{physical_progress:.2f}%")
with c3:
    st.metric("Financial Progress", f"{financial_progress:.2f}%")
with c4:
    st.metric("Variance", f"{variance:+.2f} pp")

# Interpretation
if variance < -10:
    st.error(
        f"🔴 Financial progress is significantly ahead of physical progress "
        f"by {abs(variance):.2f} percentage points."
    )
elif variance < 0:
    st.warning(
        f"🟡 Financial progress is ahead of physical progress by "
        f"{abs(variance):.2f} percentage points."
    )
elif variance > 10:
    st.warning(
        f"🟠 Physical progress is significantly ahead of financial progress "
        f"by {variance:.2f} percentage points."
    )
elif variance > 0:
    st.info(
        f"🔵 Physical progress is ahead of financial progress by "
        f"{variance:.2f} percentage points."
    )
else:
    st.success("🟢 Physical and financial progress are aligned.")

# Chart
st.divider()
st.subheader("📈 Physical vs Financial Progress by Activity")

fig = go.Figure()
fig.add_trace(
    go.Bar(
        x=data["activity"],
        y=data["physical_progress"],
        name="Physical Progress",
        text=[f"{x:.0f}%" for x in data["physical_progress"]],
        textposition="auto",
    )
)
fig.add_trace(
    go.Bar(
        x=data["activity"],
        y=data["financial_progress"],
        name="Financial Progress",
        text=[f"{x:.0f}%" for x in data["financial_progress"]],
        textposition="auto",
    )
)
fig.update_layout(
    barmode="group",
    height=430,
    yaxis={"title": "Progress (%)", "range": [0, 100]},
    xaxis={"title": "Activity"},
)
st.plotly_chart(fig, use_container_width=True)

# Activity table
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

st.dataframe(display_data, use_container_width=True, hide_index=True)

# Progress value
st.subheader("💰 Progress Value")

v1, v2, v3 = st.columns(3)

with v1:
    st.metric("Contract Value", f"PKR {contract_amount:,.0f}")
with v2:
    st.metric("Physical Progress Value", f"PKR {physical_value:,.0f}")
with v3:
    st.metric("Financial Progress Value", f"PKR {financial_value:,.0f}")

# BOQ
with st.expander("📋 View Project BOQ"):
    st.dataframe(boq, use_container_width=True, hide_index=True)

# AI image analysis
st.divider()
st.subheader("📷 AI Site Evidence Analysis")

st.write(
    "Upload a construction photograph. The AI identifies the visible "
    "construction activity and stage and gives a visual estimate for "
    "engineer review."
)

uploaded_file = st.file_uploader(
    "Upload a construction site photograph",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
    image = Image.open(uploaded_file)

    left, right = st.columns(2)

    with left:
        st.image(
            image,
            caption="Uploaded Site Evidence",
            use_container_width=True,
        )

    with right:
        if not GEMINI_AVAILABLE:
            st.info(
                "Gemini AI is not installed yet. The dashboard and "
                "image upload work without it."
            )
        elif not st.secrets.get("GEMINI_API_KEY", ""):
            st.info(
                "Add GEMINI_API_KEY to Streamlit Secrets to enable "
                "AI image analysis."
            )
        else:
            if st.button("🔍 Analyze Site Image", type="primary"):
                try:
                    client = genai.Client(
                        api_key=st.secrets["GEMINI_API_KEY"]
                    )

                    prompt = '''
You are a construction engineering assistant.

Analyze this construction site image and provide:

1. Detected Construction Component
2. Construction Stage
3. Visual Progress Estimate (0-100%)
4. Confidence (High/Medium/Low)
5. Visible Evidence
6. What Cannot Be Confirmed From The Image
7. Engineer Verification Note

Rules:
- Estimate only what is visually supported.
- Do not claim exact quantity, thickness, compaction, payment,
  or completed BOQ quantity from an image alone.
- Machinery presence is not proof that work is complete.
- The visual estimate is supporting evidence, not final certified
  physical progress.
'''

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            types.Part.from_bytes(
                                data=uploaded_file.getvalue(),
                                mime_type=uploaded_file.type,
                            ),
                            prompt,
                        ],
                    )

                    st.markdown(response.text)
                    st.success(
                        "AI assessment generated. Engineer verification "
                        "is required before using it as verified progress."
                    )

                except Exception as exc:
                    st.error(
                        "AI analysis failed. Check the Gemini API key "
                        "and Streamlit configuration."
                    )
                    st.caption(str(exc))

# Engineer verification
st.divider()
st.subheader("👷 Engineer Verification")

st.write(
    "Review the AI estimate and record the engineer's verified "
    "physical progress."
)

selected_activity = st.selectbox(
    "Select Activity",
    data["activity"].tolist(),
)

selected_row = data[data["activity"] == selected_activity].iloc[0]

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
        f"{selected_activity}: verified progress recorded at "
        f"{verified_progress:.1f}% for this session."
    )
    st.caption(
        "Prototype note: verification is currently session-based; "
        "permanent database storage will be added later."
    )

# Final interpretation
st.divider()
st.subheader("🧠 Project Monitoring Interpretation")

if variance < -10:
    interpretation = (
        "Financial progress is substantially ahead of physical progress. "
        "Review supporting measurements and financial records."
    )
elif variance < 0:
    interpretation = (
        "Financial progress is ahead of physical progress. Review the "
        "relevant measurements and financial records in project context."
    )
elif variance > 10:
    interpretation = (
        "Physical progress is substantially ahead of financial progress. "
        "Review whether financial reporting or claims are lagging."
    )
elif variance > 0:
    interpretation = (
        "Physical progress is ahead of financial progress. Review whether "
        "financial reporting or claims are lagging."
    )
else:
    interpretation = "Physical and financial progress are aligned."

st.write(interpretation)

st.caption(
    "Prototype: AI image analysis is supporting evidence. Final physical "
    "progress should be based on engineer-verified quantities, measurements "
    "and BOQ weights."
)
