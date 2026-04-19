import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="LA Crime Analytics",
    page_icon="🔍",
    layout="wide",
)

st.markdown("""
    <style>
    .kpi-box {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px 24px;
        margin-bottom: 8px;
    }
    .kpi-label {
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.08em;
        color: #6b7280;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #0079F2;
        line-height: 1.1;
    }
    .kpi-value-red { color: #A60808 !important; }
    .kpi-value-str { color: #0079F2 !important; font-size: 22px !important; }
    </style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA LOADING & PREPROCESSING
# ─────────────────────────────────────────────

@st.cache_data(show_spinner="Loading and processing crime data…")
def load_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)

    # Convert date strings to datetime
    for col in ["Date Rptd", "DATE OCC"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Identifier function
    def generate_custom_id(index):
        return f"CRIME_EVENT_{index}"
    df["Internal_ID"] = df.index.map(generate_custom_id)

    # Drop invalid victim ages
    df = df.dropna(subset=["Vict Age"])
    df = df[df["Vict Age"] > 0]

    # String operations
    df["AREA NAME"] = df["AREA NAME"].str.upper().str.strip()
    if "Crm Cd Desc" in df.columns:
        df["Crime_Category"] = df["Crm Cd Desc"].str.split(" ").str[0]
    else:
        df["Crime_Category"] = "UNKNOWN"

    return df


@st.cache_data(show_spinner=False)
def compute_priority(df: pd.DataFrame) -> pd.DataFrame:
    """Automated priority trigger — same logic as the Python script."""
    counts = df["AREA NAME"].value_counts()
    threshold = counts.quantile(0.75)
    high_priority_areas = counts[counts >= threshold].index.tolist()
    df = df.copy()
    df["Priority"] = df["AREA NAME"].apply(
        lambda x: "HIGH" if x in high_priority_areas else "STANDARD"
    )
    return df


# ─────────────────────────────────────────────
# SIDEBAR — FILE UPLOAD
# ─────────────────────────────────────────────

st.sidebar.title("LA Crime Analytics")
st.sidebar.markdown("Upload the **Crime_Data_from_2020_to_Present.csv** dataset to begin.")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

default_path = os.path.join(
    os.path.expanduser("~"),
    "Downloads",
    "Crime_Data_from_2020_to_Present.csv",
)

df = None

if uploaded_file is not None:
    df = load_data(uploaded_file)
    df = compute_priority(df)
elif os.path.exists(default_path):
    df = load_data(default_path)
    df = compute_priority(df)


# ─────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────

st.title("LA Crime Analytics Dashboard")
st.caption("Mission-critical intelligence dashboard · Crime Data 2020 – Present")
st.divider()

if df is None:
    st.info(
        "No data loaded yet. Upload your CSV using the sidebar, or place it at:\n\n"
        f"`{default_path}`",
        icon="ℹ️",
    )
    st.stop()

# ── Statistics ──────────────────────────────
mean_age       = df["Vict Age"].mean()
median_age     = df["Vict Age"].median()
quantile_75    = df["Vict Age"].quantile(0.75)
percentile_90  = np.percentile(df["Vict Age"], 90)
total_crimes   = len(df)

priority_counts   = df[["AREA NAME", "Priority"]].drop_duplicates()
high_priority_n   = (priority_counts["Priority"] == "HIGH").sum()
std_priority_n    = (priority_counts["Priority"] == "STANDARD").sum()

top_category = (
    df["Crime_Category"].value_counts().idxmax()
    if "Crime_Category" in df.columns else "N/A"
)

# ── KPI Row ─────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-label">Total Crimes</div>
        <div class="kpi-value">{total_crimes:,}</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-label">Mean Victim Age</div>
        <div class="kpi-value">{mean_age:.1f}</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-label">High-Priority Areas</div>
        <div class="kpi-value kpi-value-red">{high_priority_n}</div>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-label">Top Crime Category</div>
        <div class="kpi-value kpi-value-str">{top_category}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Crime Counts by Area ─────────────────────
area_summary = (
    df.groupby("AREA NAME")
    .agg(
        Total_Crimes=("Vict Age", "count"),
        Avg_Age=("Vict Age", "mean"),
        Min_Age=("Vict Age", "min"),
        Max_Age=("Vict Age", "max"),
    )
    .reset_index()
    .sort_values("Total_Crimes", ascending=False)
)
area_summary = area_summary.merge(
    priority_counts, on="AREA NAME", how="left"
)

c1, c2 = st.columns(2)

with c1:
    st.subheader("Crime Counts by Area")
    fig_area = px.bar(
        area_summary.head(20),
        x="AREA NAME",
        y="Total_Crimes",
        color="Priority",
        color_discrete_map={"HIGH": "#A60808", "STANDARD": "#0079F2"},
        labels={"Total_Crimes": "Total Crimes", "AREA NAME": "Area"},
    )
    fig_area.update_layout(
        xaxis_tickangle=-45,
        legend_title="Priority",
        margin=dict(t=10, b=10),
        height=380,
    )
    st.plotly_chart(fig_area, use_container_width=True)

# ── Top Crime Categories ─────────────────────
with c2:
    st.subheader("Top 10 Crime Categories")
    cat_counts = df["Crime_Category"].value_counts().head(10).reset_index()
    cat_counts.columns = ["Category", "Count"]
    fig_cat = px.pie(
        cat_counts,
        names="Category",
        values="Count",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_cat.update_layout(margin=dict(t=10, b=10), height=380)
    st.plotly_chart(fig_cat, use_container_width=True)

# ── Age Distribution ─────────────────────────
c3, c4 = st.columns(2)

with c3:
    st.subheader("Victim Age Distribution")
    bins   = [0, 17, 24, 34, 44, 54, 64, 200]
    labels = ["0-17", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    age_buckets = pd.cut(df["Vict Age"], bins=bins, labels=labels)
    age_dist = age_buckets.value_counts().sort_index().reset_index()
    age_dist.columns = ["Age Group", "Count"]

    st.markdown(
        f"**Mean:** {mean_age:.2f} · "
        f"**Median:** {median_age:.0f} · "
        f"**75th pct:** {quantile_75:.0f} · "
        f"**90th pct:** {percentile_90:.0f}"
    )

    fig_age = px.bar(
        age_dist,
        x="Age Group",
        y="Count",
        color_discrete_sequence=["#795EFF"],
        labels={"Count": "Number of Victims"},
    )
    fig_age.update_layout(margin=dict(t=10, b=10), height=340)
    st.plotly_chart(fig_age, use_container_width=True)

# ── Priority Breakdown ───────────────────────
with c4:
    st.subheader("Priority Classification by Area")
    fig_prio = px.bar(
        area_summary.sort_values("Total_Crimes", ascending=True),
        x="Total_Crimes",
        y="AREA NAME",
        color="Priority",
        orientation="h",
        color_discrete_map={"HIGH": "#A60808", "STANDARD": "#0079F2"},
        labels={"Total_Crimes": "Total Crimes", "AREA NAME": ""},
    )
    fig_prio.update_layout(margin=dict(t=10, b=10), height=380, legend_title="Priority")
    st.plotly_chart(fig_prio, use_container_width=True)

st.divider()

# ── Full Area Data Table ─────────────────────
st.subheader("Area Detail Table")

display_df = area_summary.copy()
display_df["Avg_Age"] = display_df["Avg_Age"].round(1)
display_df.columns = ["Area Name", "Total Crimes", "Avg Age", "Min Age", "Max Age", "Priority"]
display_df = display_df.reset_index(drop=True)

def color_priority(val):
    if val == "HIGH":
        return "background-color: #fff0f0; color: #A60808; font-weight: bold;"
    return "background-color: #f0f6ff; color: #0079F2; font-weight: bold;"

styled = display_df.style.applymap(color_priority, subset=["Priority"])
st.dataframe(styled, use_container_width=True, height=420)

# CSV download
csv_data = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Table as CSV",
    data=csv_data,
    file_name="crime_area_summary.csv",
    mime="text/csv",
)

st.divider()

# ── Area Priority Checker ────────────────────
st.subheader("Check Area Priority")
st.caption("Enter an area name to look up its priority classification (mirrors the check_area_priority() function).")

col_input, col_btn = st.columns([3, 1])
with col_input:
    user_area = st.text_input("Area Name", placeholder="e.g. HOLLYWOOD", label_visibility="collapsed")
with col_btn:
    check_btn = st.button("Check Priority", use_container_width=True)

if check_btn or user_area:
    query = user_area.upper().strip()
    if query:
        result = df[df["AREA NAME"] == query]["Priority"].unique()
        if len(result) > 0:
            priority_val = result[0]
            color = "#A60808" if priority_val == "HIGH" else "#009118"
            st.markdown(
                f"Area **{query}** is classified as: "
                f"<span style='color:{color}; font-weight:700; font-size:18px'>{priority_val}</span> priority.",
                unsafe_allow_html=True,
            )
        else:
            available = sorted(df["AREA NAME"].unique().tolist())
            st.warning(
                f"Area **{query}** not found. Available areas:\n\n"
                + ", ".join(available)
            )

st.divider()

# ── Export processed data ────────────────────
if st.button("Export Processed Data to CSV"):
    out_path = "processed_crime_data_with_priority.csv"
    df.to_csv(out_path, index=False)
    st.success(f"Exported to `{out_path}`")
    full_csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Full Processed CSV",
        data=full_csv,
        file_name="processed_crime_data_with_priority.csv",
        mime="text/csv",
    )
