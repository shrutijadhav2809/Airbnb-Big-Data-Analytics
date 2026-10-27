
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------
# Configuration
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "airbnb_cleaned.csv"
RESULTS_DIR = BASE_DIR / "spark_results"

st.set_page_config(
    page_title="StayScope | Airbnb Analytics",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# Styling
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.stApp {
    background: #F7F8FA;
}
.block-container {
    padding-top: 1.6rem;
    padding-bottom: 2.5rem;
    max-width: 1500px;
}
.hero {
    background: linear-gradient(120deg, #183D3D, #285D56);
    padding: 28px 30px;
    border-radius: 18px;
    color: white;
    margin-bottom: 22px;
}
.hero h1 {
    color: white;
    font-size: 34px;
    margin: 0;
}
.hero p {
    color: #DDEBE5;
    margin: 8px 0 0 0;
}
.metric-card {
    background: white;
    border: 1px solid #E8EAED;
    border-radius: 14px;
    padding: 18px 20px;
    min-height: 112px;
}
.metric-label {
    color: #6B7280;
    font-size: 13px;
}
.metric-value {
    color: #193C3A;
    font-size: 28px;
    font-weight: 700;
    margin-top: 7px;
}
.section-title {
    color: #193C3A;
    font-size: 21px;
    font-weight: 700;
    margin: 14px 0;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #E8EAED;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# Load the actual dataset
# --------------------------------------------------
@st.cache_data
def load_data(file_path, modified_time):
    data = pd.read_csv(file_path)

    # Convert numeric fields safely.
    for column in ["price", "stars", "numberOfGuests",
                   "latitude", "longitude"]:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column], errors="coerce"
            )

    return data


if not DATA_FILE.exists():
    st.error(f"Dataset not found: {DATA_FILE}")
    st.info(
        "Place airbnb_cleaned.csv in the same folder as app.py."
    )
    st.stop()

df = load_data(str(DATA_FILE), DATA_FILE.stat().st_mtime)

required_columns = {
    "name", "location", "state", "roomType",
    "numberOfGuests", "price", "stars"
}
missing_columns = required_columns - set(df.columns)

if missing_columns:
    st.error(
        "Dataset columns are different from expected. Missing: "
        + ", ".join(sorted(missing_columns))
    )
    st.write("Columns found:", df.columns.tolist())
    st.stop()

# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------
st.sidebar.markdown("## 🏡 StayScope")
st.sidebar.caption("Airbnb Listing Intelligence")
st.sidebar.divider()

search_text = st.sidebar.text_input(
    "Search listings",
    placeholder="Property or location...",
)

states = sorted(df["state"].dropna().astype(str).unique())
selected_states = st.sidebar.multiselect(
    "Choose states",
    states,
    default=[],
)

room_types = sorted(
    df["roomType"].dropna().astype(str).unique()
)
selected_rooms = st.sidebar.multiselect(
    "Room type",
    room_types,
    default=[],
)

valid_prices = df["price"].dropna()
if not valid_prices.empty:
    min_price = float(valid_prices.min())
    max_price = float(valid_prices.max())

    if min_price < max_price:
        price_range = st.sidebar.slider(
            "Price range",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price),
        )
    else:
        price_range = (min_price, max_price)
else:
    price_range = (0.0, 0.0)

# --------------------------------------------------
# Apply filters
# --------------------------------------------------
filtered = df.copy()

if search_text.strip():
    search_columns = ["name", "location", "state"]
    mask = pd.Series(False, index=filtered.index)

    for column in search_columns:
        mask |= filtered[column].astype(str).str.contains(
            search_text.strip(),
            case=False,
            na=False,
            regex=False,
        )

    filtered = filtered[mask]

if selected_states:
    filtered = filtered[
        filtered["state"].astype(str).isin(selected_states)
    ]

if selected_rooms:
    filtered = filtered[
        filtered["roomType"].astype(str).isin(selected_rooms)
    ]

filtered = filtered[
    filtered["price"].between(
        price_range[0], price_range[1], inclusive="both"
    )
]

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("""
<div class="hero">
  <h1>Find your next insight.</h1>
  <p>
    Explore Indian Airbnb listings, compare prices and uncover
    patterns using your Big Data Analytics project.
  </p>
</div>
""", unsafe_allow_html=True)

st.caption(
    "Metrics and charts below are calculated from the selected "
    "rows of airbnb_cleaned.csv."
)

# --------------------------------------------------
# KPI cards
# --------------------------------------------------
total_listings = len(filtered)
average_price = filtered["price"].mean()
average_rating = filtered["stars"].mean()
states_count = filtered["state"].nunique()

def metric_card(label, value):
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

c1, c2, c3, c4 = st.columns(4)

with c1:
    metric_card("LISTINGS MATCHED", f"{total_listings:,}")

with c2:
    price_text = (
        f"{average_price:,.2f}"
        if pd.notna(average_price) else "N/A"
    )
    metric_card("AVERAGE LISTED PRICE", price_text)

with c3:
    rating_text = (
        f"{average_rating:.2f} / 5"
        if pd.notna(average_rating) else "N/A"
    )
    metric_card("AVERAGE STARS", rating_text)

with c4:
    metric_card("STATES REPRESENTED", f"{states_count:,}")

st.write("")

# --------------------------------------------------
# Analytics charts
# --------------------------------------------------
st.markdown(
    '<div class="section-title">Explore the market</div>',
    unsafe_allow_html=True,
)

chart_left, chart_right = st.columns(2)

with chart_left:
    st.subheader("Average listed price by state")

    state_prices = (
        filtered.dropna(subset=["state", "price"])
        .groupby("state", as_index=False)
        .agg(
            average_price=("price", "mean"),
            listings=("price", "size"),
        )
        .sort_values("average_price", ascending=False)
    )

    if not state_prices.empty:
        fig = px.bar(
            state_prices,
            x="state",
            y="average_price",
            hover_data=["listings"],
            labels={
                "state": "State",
                "average_price": "Average listed price",
                "listings": "Listings",
            },
            color="average_price",
            color_continuous_scale=["#C7DED5", "#285D56"],
        )
        fig.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=25, b=10),
            xaxis_tickangle=-35,
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No price data for the current filters.")

with chart_right:
    st.subheader("Listings by room type")

    room_counts = (
        filtered.dropna(subset=["roomType"])
        .groupby("roomType", as_index=False)
        .size()
        .rename(columns={"size": "listings"})
        .sort_values("listings", ascending=False)
    )

    if not room_counts.empty:
        fig = px.pie(
            room_counts,
            names="roomType",
            values="listings",
            hole=0.58,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=25, b=10),
            legend_title_text="Room type",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No room-type data for the current filters.")

# --------------------------------------------------
# Guest capacity analysis
# --------------------------------------------------
st.subheader("Price by guest capacity")

guest_data = (
    filtered.dropna(subset=["numberOfGuests", "price"])
    .groupby("numberOfGuests", as_index=False)
    .agg(
        average_price=("price", "mean"),
        listings=("price", "size"),
    )
    .sort_values("numberOfGuests")
)

if not guest_data.empty:
    fig = px.line(
        guest_data,
        x="numberOfGuests",
        y="average_price",
        markers=True,
        hover_data=["listings"],
        labels={
            "numberOfGuests": "Guest capacity",
            "average_price": "Average listed price",
            "listings": "Listings",
        },
    )
    fig.update_traces(line_color="#285D56")
    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No guest-capacity data for the current filters.")

# --------------------------------------------------
# Listings table and CSV download
# --------------------------------------------------
st.markdown(
    '<div class="section-title">Explore listings</div>',
    unsafe_allow_html=True,
)

sort_by = st.selectbox(
    "Sort listings by",
    ["price", "stars", "name", "state"],
    index=0,
)

ascending = st.checkbox(
    "Sort ascending",
    value=True,
)

sorted_data = filtered.sort_values(
    sort_by,
    ascending=ascending,
    na_position="last",
)

st.caption(f"Showing {len(sorted_data):,} matching listings.")

st.dataframe(
    sorted_data,
    use_container_width=True,
    hide_index=True,
    height=380,
)

st.download_button(
    "⬇ Download filtered listings (CSV)",
    data=sorted_data.to_csv(index=False).encode("utf-8"),
    file_name="airbnb_filtered_listings.csv",
    mime="text/csv",
    use_container_width=False,
)

# --------------------------------------------------
# Analytics export
# --------------------------------------------------
st.markdown(
    '<div class="section-title">Download analytics</div>',
    unsafe_allow_html=True,
)

export_left, export_right = st.columns(2)

with export_left:
    st.download_button(
        "⬇ Download state-wise analytics",
        data=state_prices.to_csv(index=False).encode("utf-8"),
        file_name="airbnb_price_by_state.csv",
        mime="text/csv",
    )

with export_right:
    st.download_button(
        "⬇ Download room-type analytics",
        data=room_counts.to_csv(index=False).encode("utf-8"),
        file_name="airbnb_room_type_counts.csv",
        mime="text/csv",
    )

# --------------------------------------------------
# Pipeline status: do not pretend to have live services
# --------------------------------------------------
st.markdown(
    '<div class="section-title">Big Data pipeline</div>',
    unsafe_allow_html=True,
)

hdfs_output = (
    "HDFS dataset path: /airbnb/input/airbnb_cleaned.csv"
)
mapreduce_output = (
    "HDFS Word Count output: "
    "/airbnb/wordcount/output/part-r-00000"
)

pipeline = [
    ("Dataset", "Available", "Local cleaned CSV loaded by this app."),
    (
        "Hadoop HDFS",
        "Previously verified",
        hdfs_output,
    ),
    (
        "MapReduce",
        "Previously verified",
        mapreduce_output,
    ),
    (
        "Apache Spark",
        "Previously executed",
        "spark_analytics.py and spark_results/ were created.",
    ),
    (
        "Cassandra",
        "Pending",
        "Database integration has not yet been verified.",
    ),
]

for name, status, detail in pipeline:
    with st.container(border=True):
        left, middle, right = st.columns([1.3, 1.5, 4])
        left.markdown(f"**{name}**")
        middle.write(status)
        right.caption(detail)

st.caption(
    "Pipeline labels reflect the recorded implementation status, "
    "not continuous live health checks. The dashboard currently "
    "reads the local CSV and computes its own interactive charts."
)

st.divider()
st.caption(
    "StayScope · Airbnb Big Data Analytics · "
    "Prices use the units recorded in the source dataset."
)
