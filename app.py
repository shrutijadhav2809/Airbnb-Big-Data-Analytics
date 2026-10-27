from pathlib import Path
import hashlib
import hmac
import os
import secrets
import sqlite3
import subprocess

import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------
# Configuration
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "airbnb_cleaned.csv"
RESULTS_DIR = BASE_DIR / "spark_results"
AUTH_DB = BASE_DIR / "stayscope_users.db"

st.set_page_config(
    page_title="StayScope | Airbnb Analytics",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# Premium UI styling
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
:root { --airbnb:#ff385c; --airbnb-dark:#e31c5f; --ink:#222222; --muted:#717171; --line:#ebebeb; --soft:#fff5f6; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; color:var(--ink); }
.stApp { background:#ffffff; color:var(--ink); }
[data-testid="stHeader"] { background:rgba(255,255,255,.94); }
.block-container { padding-top:1.3rem; padding-bottom:3rem; max-width:1600px; }
section[data-testid="stSidebar"] { background:#fff; border-right:1px solid #ebebeb; }
section[data-testid="stSidebar"] * { color:#222 !important; }
section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] [data-baseweb="select"] > div { background:#fff !important; border:1px solid #b0b0b0 !important; border-radius:12px !important; }
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color:#222 !important; font-weight:600; }
.hero { position:relative; overflow:hidden; padding:34px 36px; border-radius:26px; background:linear-gradient(115deg,#ff385c 0%,#e31c5f 58%,#bd1e59 100%); border:1px solid rgba(227,28,95,.12); box-shadow:0 18px 42px rgba(227,28,95,.15); margin:4px 0 20px; }
.hero:after { content:""; position:absolute; width:270px; height:270px; right:4%; top:-115px; border:1px solid rgba(255,255,255,.48); border-radius:50%; box-shadow:0 0 0 22px rgba(255,255,255,.08),0 0 0 48px rgba(255,255,255,.06); animation:orbit 22s linear infinite; pointer-events:none; }
.hero h1 { color:#fff !important; font-size:clamp(2rem,3.2vw,3.15rem); letter-spacing:-1.5px; line-height:1.08; margin:0; }
.hero p { color:#fff !important; font-size:1rem; margin:12px 0 0; max-width:760px; }
.eyebrow { color:#fff; font-size:.75rem; letter-spacing:2px; font-weight:800; text-transform:uppercase; margin-bottom:12px; }
.section-title { color:#222 !important; font-size:1.3rem; font-weight:800; margin:22px 0 12px; letter-spacing:-.4px; }
.metric-card { position:relative; overflow:hidden; background:#fff; border:1px solid #ebebeb; border-radius:18px; padding:20px 21px; min-height:132px; box-shadow:0 7px 22px rgba(0,0,0,.045); transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease; }
.metric-card:hover { transform:translateY(-4px); border-color:rgba(255,56,92,.42); box-shadow:0 14px 30px rgba(0,0,0,.08); }
.metric-card:after { content:""; position:absolute; width:100px; height:100px; border-radius:50%; right:-38px; bottom:-55px; background:rgba(255,56,92,.07); }
.metric-label { color:#444444; font-size:.85rem; letter-spacing:1px; font-weight:800; }
.metric-value { color:#222222; font-size:clamp(1.6rem,2vw,2.2rem); font-weight:800; margin-top:12px; letter-spacing:-.5px; }
.metric-icon { float:right; font-size:1.3rem; color:var(--airbnb); }
.insight-card { height:100%; border:1px solid #ebebeb; border-radius:16px; background:linear-gradient(145deg,#fff,#fff8f9); padding:18px; box-shadow:0 6px 20px rgba(0,0,0,.035); }
.insight-label { color:#717171; font-size:.73rem; font-weight:800; letter-spacing:.8px; text-transform:uppercase; }
.insight-value { color:#222; font-size:1.2rem; font-weight:800; margin-top:8px; }
.insight-detail { color:#717171; font-size:.86rem; margin-top:6px; }
div[data-testid="stDataFrame"] { border:1px solid #ebebeb; border-radius:14px; overflow:hidden; }
.stButton > button, .stDownloadButton > button { border-radius:12px; border:1px solid #ff385c; color:#e31c5f; background:#fff; font-weight:700; transition:all .2s ease; }
.stButton > button:hover, .stDownloadButton > button:hover { transform:translateY(-2px); border-color:#e31c5f; background:#fff5f6; color:#bd1e59; }
.stButton > button[kind="primary"], button[kind="primaryFormSubmit"] { background:#ff385c; color:#fff; border-color:#ff385c; }
.stButton > button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover { background:#e31c5f; color:#fff; }
div[data-testid="stPlotlyChart"] { border:1px solid #ebebeb; border-radius:16px; padding:8px; background:#fff; box-shadow:0 5px 18px rgba(0,0,0,.025); }
.auth-wrap { max-width:510px; margin:5vh auto 0; padding:30px; border:1px solid #ebebeb; border-radius:24px; background:linear-gradient(145deg,#fff,#fff5f6); box-shadow:0 18px 50px rgba(0,0,0,.07); }
.auth-title { font-size:2rem; font-weight:800; color:#222; margin:0; }
.auth-sub { color:#717171; margin:8px 0 18px; }
.status-pill { display:inline-block; padding:5px 10px; border-radius:100px; background:#fff5f6; border:1px solid #ffd5dd; color:#bd1e59; font-size:.75rem; font-weight:700; }

/* Keep Sign in and Create account tabs visible in Airbnb red */
.stTabs [data-baseweb="tab"] {
    color: #ff385c !important;
    font-weight: 700 !important;
    opacity: 1 !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #e31c5f !important;
}

.stTabs [aria-selected="true"] {
    color: #ff385c !important;
}

@keyframes orbit { from { transform:rotate(0deg); } to { transform:rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { *,*::before,*::after { animation:none !important; transition:none !important; } }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Local demo authentication
# Passwords are stored as PBKDF2 hashes, never plaintext.
# For public/production deployment, use a managed identity provider.
# --------------------------------------------------
def init_auth_db():
    with sqlite3.connect(AUTH_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

def hash_password(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 310_000
    ).hex()

def register_user(username: str, password: str):
    username = username.strip().lower()
    salt = secrets.token_hex(16)
    digest = hash_password(password, salt)
    try:
        with sqlite3.connect(AUTH_DB) as conn:
            conn.execute(
                "INSERT INTO users(username,password_hash,salt) VALUES(?,?,?)",
                (username, digest, salt),
            )
        return True, "Account created. You can sign in now."
    except sqlite3.IntegrityError:
        return False, "That username already exists. Please choose another."

def verify_user(username: str, password: str) -> bool:
    with sqlite3.connect(AUTH_DB) as conn:
        row = conn.execute(
            "SELECT password_hash,salt FROM users WHERE username=?",
            (username.strip().lower(),),
        ).fetchone()
    if not row:
        return False
    candidate = hash_password(password, row[1])
    return hmac.compare_digest(candidate, row[0])

init_auth_db()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

def render_auth():
    st.markdown("""
    <div class="auth-wrap">
      <div class="eyebrow">AIRBNB LISTING INTELLIGENCE</div>
      <div class="auth-title">🏡 StayScope</div>
      <div class="auth-sub">Your space to explore the Indian short-stay market.</div>
      <span class="status-pill">Private workspace · Local sign-in</span>
    </div>
    """, unsafe_allow_html=True)
    left, center, right = st.columns([1, 1.25, 1])
    with center:
        tab_login, tab_register = st.tabs(["Sign in", "Create account"])
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
            if submitted:
                if verify_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username.strip().lower()
                    st.rerun()
                else:
                    st.error("Sign-in failed. Check your username and password.")
        with tab_register:
            with st.form("register_form"):
                new_username = st.text_input("Choose a username", placeholder="At least 3 characters")
                new_password = st.text_input("Create password", type="password", placeholder="At least 8 characters")
                confirm_password = st.text_input("Confirm password", type="password")
                create = st.form_submit_button("Create account", use_container_width=True)
            if create:
                if len(new_username.strip()) < 3:
                    st.error("Username must contain at least 3 characters.")
                elif len(new_password) < 8:
                    st.error("Use a password with at least 8 characters.")
                elif new_password != confirm_password:
                    st.error("The passwords do not match.")
                else:
                    ok, message = register_user(new_username, new_password)
                    (st.success if ok else st.error)(message)
    st.caption("Prototype authentication for a local academic project. User records are stored in stayscope_users.db next to app.py.")

if not st.session_state.authenticated:
    render_auth()
    st.stop()

# --------------------------------------------------
# Load actual dataset
# --------------------------------------------------
@st.cache_data
def load_data(file_path, modified_time):
    data = pd.read_csv(file_path)
    for column in ["price", "stars", "numberOfGuests", "latitude", "longitude"]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return data

if not DATA_FILE.exists():
    st.error(f"Dataset not found: {DATA_FILE}")
    st.info("Place airbnb_cleaned.csv in the same folder as app.py.")
    st.stop()

df = load_data(str(DATA_FILE), DATA_FILE.stat().st_mtime)
required_columns = {"name", "location", "state", "roomType", "numberOfGuests", "price", "stars"}
missing_columns = required_columns - set(df.columns)
if missing_columns:
    st.error("Dataset columns are different from expected. Missing: " + ", ".join(sorted(missing_columns)))
    st.write("Columns found:", df.columns.tolist())
    st.stop()

# --------------------------------------------------
# Sidebar and filters
# --------------------------------------------------
st.sidebar.markdown("## 🏡 StayScope")
st.sidebar.caption("AIRBNB LISTING INTELLIGENCE")
st.sidebar.markdown(f"Signed in as **{st.session_state.username}**")
if st.sidebar.button("Log out", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()
st.sidebar.divider()

def reset_filters():
    st.session_state["search_text"] = ""
    st.session_state["selected_states"] = []
    st.session_state["selected_rooms"] = []
    st.session_state["price_range"] = (float(valid_prices.min()), float(valid_prices.max())) if not valid_prices.empty else (0.0, 0.0)

search_text = st.sidebar.text_input("Search listings", placeholder="Property or location...", key="search_text")
states = sorted(df["state"].dropna().astype(str).unique())
selected_states = st.sidebar.multiselect("Choose states", states, default=[], key="selected_states")
room_types = sorted(df["roomType"].dropna().astype(str).unique())
selected_rooms = st.sidebar.multiselect("Room type", room_types, default=[], key="selected_rooms")

valid_prices = df["price"].dropna()
if not valid_prices.empty:
    min_price, max_price = float(valid_prices.min()), float(valid_prices.max())
    if min_price < max_price:
        price_range = st.sidebar.slider("Price range", min_value=min_price, max_value=max_price, value=(min_price, max_price), key="price_range")
    else:
        price_range = (min_price, max_price)
else:
    price_range = (0.0, 0.0)

st.sidebar.button("↺ Reset all filters", on_click=reset_filters, use_container_width=True)
st.sidebar.caption(f"{len(df):,} listings in the dataset")

filtered = df.copy()
if search_text.strip():
    mask = pd.Series(False, index=filtered.index)
    for column in ["name", "location", "state"]:
        mask |= filtered[column].astype(str).str.contains(search_text.strip(), case=False, na=False, regex=False)
    filtered = filtered[mask]
if selected_states:
    filtered = filtered[filtered["state"].astype(str).isin(selected_states)]
if selected_rooms:
    filtered = filtered[filtered["roomType"].astype(str).isin(selected_rooms)]
filtered = filtered[filtered["price"].between(price_range[0], price_range[1], inclusive="both")]

# --------------------------------------------------
# Hero
# --------------------------------------------------
hero_left, hero_right = st.columns([5, 1])
with hero_left:
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">DATA-DRIVEN STAYS · INDIA</div>
      <h1>Find your next insight.</h1>
      <p>Explore listings, compare price patterns and uncover market signals across India's short-stay destinations.</p>
    </div>
    """, unsafe_allow_html=True)
with hero_right:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='status-pill'>● Workspace active</div><p style='color:#91a8b5;font-size:.8rem;margin-top:12px'>Welcome back,<br><b>{st.session_state.username}</b></p>", unsafe_allow_html=True)

st.caption("Live dashboard calculations use the selected rows from airbnb_cleaned.csv. Hadoop/Spark statuses below are historical verification notes, not live health checks.")

if filtered.empty:
    st.warning("No listings match these filters. Try a broader search or select ‘Reset all filters’ in the sidebar.")

# --------------------------------------------------
# KPI cards
# --------------------------------------------------
total_listings = len(filtered)
average_price = filtered["price"].mean()
average_rating = filtered["stars"].mean()
states_count = filtered["state"].nunique()

def metric_card(label, value, icon):
    st.markdown(
        f'<div class="metric-card"><span class="metric-icon">{icon}</span>'
        f'<div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>',
        unsafe_allow_html=True,
    )

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("LISTINGS MATCHED", f"{total_listings:,}", "⌂")
with c2:
    metric_card("AVERAGE LISTED PRICE", f"{average_price:,.2f}" if pd.notna(average_price) else "N/A", "₹")
with c3:
    metric_card("AVERAGE STARS", f"{average_rating:.2f} / 5" if pd.notna(average_rating) else "N/A", "✦")
with c4:
    metric_card("STATES REPRESENTED", f"{states_count:,}", "⌖")

st.markdown('<div class="section-title">Explore the market</div>', unsafe_allow_html=True)
chart_left, chart_right = st.columns(2)

with chart_left:
    st.subheader("Average listed price by state")
    state_prices = (
        filtered.dropna(subset=["state", "price"])
        .groupby("state", as_index=False)
        .agg(average_price=("price", "mean"), listings=("price", "size"))
        .sort_values("average_price", ascending=False)
    )
    if not state_prices.empty:
        fig = px.bar(
            state_prices, x="state", y="average_price", hover_data=["listings"],
            labels={"state": "State", "average_price": "Average listed price", "listings": "Listings"},
            color="average_price", color_continuous_scale=["#ffd5dd", "#ff385c", "#bd1e59"],
            template="plotly_white",
        )
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=25, b=10), xaxis_tickangle=-35,
                          coloraxis_showscale=False, paper_bgcolor="white", plot_bgcolor="white",
                          font=dict(color="#222222"), xaxis=dict(tickfont=dict(color="#444444"), gridcolor="#eeeeee"),
                          yaxis=dict(tickfont=dict(color="#444444"), gridcolor="#eeeeee"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No price data for the current filters.")

with chart_right:
    st.subheader("Listings by room type")
    room_counts = (
        filtered.dropna(subset=["roomType"]).groupby("roomType", as_index=False).size()
        .rename(columns={"size": "listings"}).sort_values("listings", ascending=False)
    )
    if not room_counts.empty:
        fig = px.pie(room_counts, names="roomType", values="listings", hole=0.62,
                     color_discrete_sequence=["#ff385c", "#e31c5f", "#ff8fa3", "#ffb3c1", "#7c263d", "#f7a8b8"],
                     template="plotly_white")
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=25, b=10), legend_title_text="Room type",
                          paper_bgcolor="white", plot_bgcolor="white", font=dict(color="#222222"),
                          legend=dict(font=dict(color="#333333")))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No room-type data for the current filters.")

# --------------------------------------------------
# Data-driven highlights
# --------------------------------------------------
st.markdown('<div class="section-title">Market highlights</div>', unsafe_allow_html=True)
if not filtered.empty:
    priced = filtered.dropna(subset=["price"])
    rated = filtered.dropna(subset=["stars"])
    top_state = state_prices.iloc[0] if not state_prices.empty else None
    top_room = room_counts.iloc[0] if not room_counts.empty else None
    best_value = priced.loc[priced["price"].idxmin()] if not priced.empty else None
    hi1, hi2, hi3 = st.columns(3)
    with hi1:
        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
        st.markdown('<div class="insight-label">Highest average-price state</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-value">{top_state["state"] if top_state is not None else "Not available"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-detail">Average listed price: {top_state["average_price"]:,.2f}</div>' if top_state is not None else '<div class="insight-detail">No price data for current filters.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with hi2:
        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
        st.markdown('<div class="insight-label">Most common room type</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-value">{top_room["roomType"] if top_room is not None else "Not available"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-detail">{int(top_room["listings"]):,} matching listings</div>' if top_room is not None else '<div class="insight-detail">No room-type data for current filters.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with hi3:
        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
        st.markdown('<div class="insight-label">Lowest listed price</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-value">{best_value["price"]:,.2f}</div>' if best_value is not None else '<div class="insight-value">Not available</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-detail">{str(best_value["name"])[:70]}</div>' if best_value is not None else '<div class="insight-detail">No price data for current filters.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    if not rated.empty:
        st.info(f"Analyst note: the current selection contains {len(filtered):,} listings across {filtered['state'].nunique()} states, with an average rating of {rated['stars'].mean():.2f}/5. These figures update when you change filters.")
else:
    st.info("Market highlights will appear when your filters match at least one listing.")

# --------------------------------------------------
# India market map
# --------------------------------------------------
st.markdown('<div class="section-title">Explore listings across India</div>', unsafe_allow_html=True)
if {"latitude", "longitude"}.issubset(filtered.columns):
    map_data = filtered.dropna(subset=["latitude", "longitude"]).copy()
    # Avoid plotting invalid coordinates that can break map rendering.
    map_data = map_data[map_data["latitude"].between(6, 38) & map_data["longitude"].between(68, 98)]
    if not map_data.empty:
        map_hover = [c for c in ["location", "state", "roomType", "price", "stars", "numberOfGuests"] if c in map_data.columns]
        fig_map = px.scatter_map(
            map_data,
            lat="latitude", lon="longitude",
            color="roomType" if "roomType" in map_data.columns else None,
            size="price" if "price" in map_data.columns else None,
            size_max=15,
            hover_name="name" if "name" in map_data.columns else None,
            hover_data=map_hover,
            zoom=3.4,
            center={"lat": 22.8, "lon": 79.0},
            color_discrete_sequence=["#ff385c", "#e31c5f", "#ff8fa3", "#7c263d", "#f7a8b8"],
        )
        fig_map.update_layout(
            height=520, margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="white", font=dict(color="#222222"),
            legend_title_text="Room type",
        )
        st.plotly_chart(fig_map, use_container_width=True)
        st.caption(f"Mapped {len(map_data):,} listings with valid coordinates. Map markers reflect the filtered dataset.")
    else:
        st.info("No valid India coordinates are available for the current filters.")
else:
    st.info("The dataset does not contain both latitude and longitude columns.")

# --------------------------------------------------
# Guest capacity and 3D view
# --------------------------------------------------
st.markdown('<div class="section-title">Pricing & capacity signals</div>', unsafe_allow_html=True)
guest_data = (
    filtered.dropna(subset=["numberOfGuests", "price"])
    .groupby("numberOfGuests", as_index=False)
    .agg(average_price=("price", "mean"), listings=("price", "size"))
    .sort_values("numberOfGuests")
)
if not guest_data.empty:
    fig = px.line(guest_data, x="numberOfGuests", y="average_price", markers=True, hover_data=["listings"],
                  labels={"numberOfGuests": "Guest capacity", "average_price": "Average listed price", "listings": "Listings"},
                  template="plotly_white")
    fig.update_traces(line_color="#ff385c", line_width=3, marker_size=9)
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=20, b=10),
                      paper_bgcolor="white", plot_bgcolor="white", font=dict(color="#222222"),
                      xaxis=dict(tickfont=dict(color="#444444"), gridcolor="#eeeeee"),
                      yaxis=dict(tickfont=dict(color="#444444"), gridcolor="#eeeeee"))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No guest-capacity data for the current filters.")

if {"latitude", "longitude"}.issubset(filtered.columns):
    geo_data = filtered.dropna(subset=["latitude", "longitude", "price"])
    if not geo_data.empty:
        st.subheader("Interactive 3D listing landscape")
        st.caption("Drag to rotate, scroll to zoom, and hover over points to inspect listings. This uses recorded coordinates and prices.")
        geo_data = geo_data.copy()
        geo_data["price_size"] = geo_data["price"].clip(lower=1)
        fig3d = px.scatter_3d(
            geo_data, x="longitude", y="latitude", z="price",
            color="roomType" if "roomType" in geo_data.columns else None,
            size="price_size", size_max=12,
            hover_name="name",
            hover_data={"location": True, "state": True, "stars": True, "price": ":.2f",
                        "longitude": False, "latitude": False, "price_size": False},
            template="plotly_white",
            labels={"longitude": "Longitude", "latitude": "Latitude", "price": "Listed price"},
            opacity=0.82,
        )
        fig3d.update_layout(height=560, margin=dict(l=0, r=0, t=15, b=0),
                            paper_bgcolor="white", font=dict(color="#222222"), scene=dict(
                                bgcolor="white",
                                xaxis=dict(backgroundcolor="white", gridcolor="#e8e8e8", color="#444444"),
                                yaxis=dict(backgroundcolor="white", gridcolor="#e8e8e8", color="#444444"),
                                zaxis=dict(backgroundcolor="white", gridcolor="#e8e8e8", color="#444444"),
                            ))
        st.plotly_chart(fig3d, use_container_width=True)

# --------------------------------------------------
# Property Explorer: cards + sorting + quick recommendations
# --------------------------------------------------
st.markdown('<div class="section-title">Property Explorer</div>', unsafe_allow_html=True)
st.caption("Browse the listings that match your filters. Recommendations are calculated from the current dataset selection.")

sort_label = st.selectbox(
    "Sort properties by",
    ["Price: low to high", "Price: high to low", "Highest rated", "Guest capacity", "Property name"],
    key="property_sort",
)
sort_map = {
    "Price: low to high": ("price", True),
    "Price: high to low": ("price", False),
    "Highest rated": ("stars", False),
    "Guest capacity": ("numberOfGuests", False),
    "Property name": ("name", True),
}
sort_column, sort_ascending = sort_map[sort_label]
sorted_data = filtered.sort_values(sort_column, ascending=sort_ascending, na_position="last")

if not sorted_data.empty:
    price_rows = sorted_data.dropna(subset=["price"])
    rating_rows = sorted_data.dropna(subset=["stars"])
    best_budget = price_rows.loc[price_rows["price"].idxmin()] if not price_rows.empty else None
    best_rated = rating_rows.loc[rating_rows["stars"].idxmax()] if not rating_rows.empty else None
    rec_left, rec_right = st.columns(2)
    with rec_left:
        with st.container(border=True):
            st.caption("💸 BUDGET PICK")
            if best_budget is not None:
                st.subheader(str(best_budget.get("name", "Unnamed property"))[:70])
                st.markdown(f"**{best_budget['price']:,.2f}** · {best_budget.get('location', 'Location unavailable')}")
                st.caption(f"{best_budget.get('state', 'State unavailable')} · {best_budget.get('roomType', 'Room type unavailable')}")
            else:
                st.info("No price data for this selection.")
    with rec_right:
        with st.container(border=True):
            st.caption("⭐ TOP RATED PICK")
            if best_rated is not None:
                st.subheader(str(best_rated.get("name", "Unnamed property"))[:70])
                st.markdown(f"**{best_rated['stars']:.2f} / 5** · {best_rated.get('location', 'Location unavailable')}")
                st.caption(f"{best_rated.get('state', 'State unavailable')} · Listed price: {best_rated.get('price', float('nan')):,.2f}")
            else:
                st.info("No rating data for this selection.")

    st.caption(f"Showing {len(sorted_data):,} matching properties · Displaying up to 12 cards per page.")
    page_size = 12
    page_count = max(1, (len(sorted_data) + page_size - 1) // page_size)
    page = st.number_input("Property page", min_value=1, max_value=page_count, value=1, step=1, key="property_page")
    page_rows = sorted_data.iloc[(page - 1) * page_size: page * page_size]
    card_rows = [page_rows.iloc[i:i+3] for i in range(0, len(page_rows), 3)]
    for card_row in card_rows:
        cols = st.columns(3)
        for col, (_, prop) in zip(cols, card_row.iterrows()):
            with col:
                with st.container(border=True):
                    st.markdown(f"**{str(prop.get('name', 'Unnamed property'))[:85]}**")
                    st.caption(f"📍 {prop.get('location', 'Location unavailable')}, {prop.get('state', '')}")
                    st.markdown(f"### {prop['price']:,.2f}" if pd.notna(prop.get('price')) else "### Price unavailable")
                    rating = f"⭐ {prop['stars']:.1f}/5" if pd.notna(prop.get('stars')) else "Rating unavailable"
                    guests = f"👥 {int(prop['numberOfGuests'])} guests" if pd.notna(prop.get('numberOfGuests')) else "Guest capacity unavailable"
                    st.write(f"{rating}  ·  {guests}")
                    st.caption(str(prop.get("roomType", "Room type unavailable")))

    with st.expander("View full matching dataset and download"):
        st.dataframe(sorted_data, use_container_width=True, hide_index=True, height=320)
        st.download_button(
            "⬇ Download filtered listings (CSV)",
            data=sorted_data.to_csv(index=False).encode("utf-8"),
            file_name="airbnb_filtered_listings.csv", mime="text/csv",
        )
else:
    st.info("No properties match these filters. Clear the search or reset the filters to see listings.")

# --------------------------------------------------
# Analytics exports
# --------------------------------------------------
st.markdown('<div class="section-title">Download analytics</div>', unsafe_allow_html=True)
export_left, export_right = st.columns(2)
with export_left:
    st.download_button("⬇ Download state-wise analytics", data=state_prices.to_csv(index=False).encode("utf-8"),
                       file_name="airbnb_price_by_state.csv", mime="text/csv")
with export_right:
    st.download_button("⬇ Download room-type analytics", data=room_counts.to_csv(index=False).encode("utf-8"),
                       file_name="airbnb_room_type_counts.csv", mime="text/csv")

# --------------------------------------------------
# Big Data pipeline: report verifiable local checks honestly
# --------------------------------------------------
st.markdown('<div class="section-title">Big Data pipeline</div>', unsafe_allow_html=True)
st.caption("Checks run when this page renders. A missing service is shown as not configured/unavailable; historical success is not presented as a live connection.")

def command_check(command, timeout=4):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        return result.returncode == 0, (result.stdout or result.stderr).strip()[:260]
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        return False, str(exc)[:180]

# HDFS path check: only possible when the Hadoop CLI is available in the app environment.
hdfs_ok, hdfs_detail = command_check(["hdfs", "dfs", "-test", "-e", "/airbnb/input/airbnb_cleaned.csv"])
mapreduce_ok, mapreduce_detail = command_check(["hdfs", "dfs", "-test", "-e", "/airbnb/wordcount/output/part-r-00000"])

spark_files = []
if RESULTS_DIR.exists():
    spark_files = [p for p in RESULTS_DIR.rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".json", ".parquet"}]
spark_ok = bool(spark_files)

cassandra_status = "Not configured"
cassandra_detail = "Optional integration: configure CASSANDRA_HOST and install cassandra-driver to enable a connection check."
cassandra_host = os.getenv("CASSANDRA_HOST", "").strip()
if cassandra_host:
    try:
        from cassandra.cluster import Cluster
        cluster = Cluster([cassandra_host], connect_timeout=3)
        session = cluster.connect()
        session.execute("SELECT release_version FROM system.local")
        session.shutdown()
        cluster.shutdown()
        cassandra_status = "Connected"
        cassandra_detail = f"Connection to {cassandra_host} succeeded. Data persistence still depends on configured keyspace/tables."
    except ImportError:
        cassandra_status = "Driver missing"
        cassandra_detail = "Install cassandra-driver in the active virtual environment to test connectivity."
    except Exception as exc:
        cassandra_status = "Unavailable"
        cassandra_detail = f"Connection check failed: {str(exc)[:160]}"

pipeline = [
    ("Cleaned dataset", "Available" if DATA_FILE.exists() else "Missing", str(DATA_FILE)),
    ("Hadoop HDFS", "Reachable · dataset found" if hdfs_ok else "Not verified", hdfs_detail or "HDFS dataset path: /airbnb/input/airbnb_cleaned.csv"),
    ("MapReduce", "Output found" if mapreduce_ok else "Not verified", mapreduce_detail or "Expected: /airbnb/wordcount/output/part-r-00000"),
    ("Apache Spark", "Result files found" if spark_ok else "No result files found", f"{len(spark_files)} result file(s) in {RESULTS_DIR}" if spark_ok else "Run spark_analytics.py and confirm it writes results to spark_results/"),
    ("Cassandra", cassandra_status, cassandra_detail),
]
for name, status, detail in pipeline:
    with st.container(border=True):
        left, middle, right = st.columns([1.3, 1.6, 4])
        left.markdown(f"**{name}**")
        middle.write(status)
        right.caption(detail)


# Demand forecasting results
st.divider()
st.markdown("## 📈 Demand Forecasting")

forecast_file = BASE_DIR / "advanced_results" / "demand_forecast_demo.csv"

if forecast_file.exists():
    forecast_df = pd.read_csv(forecast_file)

    if {"date", "predicted_demand", "actual_simulated_demand"}.issubset(forecast_df.columns):
        st.caption(
            "Demonstration forecast generated using synthetic data, "
            "not actual Airbnb booking records."
        )
        forecast_df["date"] = pd.to_datetime(forecast_df["date"], errors="coerce")
        forecast_df = forecast_df.dropna(subset=["date"])

        if not forecast_df.empty:
            chart_df = forecast_df.set_index("date")[
                ["predicted_demand", "actual_simulated_demand"]
            ]
            st.line_chart(chart_df)
            st.download_button(
                "Download forecasting results",
                data=forecast_df.to_csv(index=False).encode("utf-8"),
                file_name="demand_forecast_results.csv",
                mime="text/csv",
            )
        else:
            st.warning("The forecast file contains no valid dates.")
    else:
        st.warning("The forecast CSV does not contain the expected columns.")
else:
    st.info(
        
        "Forecast results are not available yet. "
        "Run demand_forecasting.py first."
    )


# Dynamic pricing recommendations
st.divider()
st.markdown("## 💰 Dynamic Pricing Recommendations")

pricing_file = BASE_DIR / "advanced_results" / "dynamic_pricing_recommendations.csv"
summary_file = BASE_DIR / "advanced_results" / "market_pricing_summary.csv"

if pricing_file.exists():
    pricing_df = pd.read_csv(pricing_file)

    required_cols = {
        "name", "state", "roomType",
        "price", "suggested_price", "pricing_signal"
    }

    if required_cols.issubset(pricing_df.columns):
        metric1, metric2, metric3 = st.columns(3)

        metric1.metric("Listings analysed", f"{len(pricing_df):,}")
        metric2.metric(
            "Average listed price",
            f"{pricing_df['price'].mean():,.2f}"
        )
        metric3.metric(
            "Average suggested price",
            f"{pricing_df['suggested_price'].mean():,.2f}"
        )

        st.caption(
            "Suggested prices are benchmark estimates based on the available "
            "listing data, not guaranteed market prices."
        )

        if "state" in pricing_df.columns:
            selected_pricing_states = st.multiselect(
                "Filter pricing recommendations by state",
                options=sorted(pricing_df["state"].dropna().astype(str).unique()),
                key="pricing_state_filter",
            )
            if selected_pricing_states:
                pricing_df = pricing_df[
                    pricing_df["state"].astype(str).isin(selected_pricing_states)
                ]

        if "pricing_signal" in pricing_df.columns:
            st.bar_chart(pricing_df["pricing_signal"].value_counts())

        st.dataframe(
            pricing_df.sort_values("suggested_price", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download dynamic pricing recommendations",
            data=pricing_df.to_csv(index=False).encode("utf-8"),
            file_name="dynamic_pricing_recommendations.csv",
            mime="text/csv",
        )

        if summary_file.exists():
            st.markdown("### Market pricing summary by state")
            summary_df = pd.read_csv(summary_file)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
    else:
        st.warning("The dynamic pricing CSV is missing expected columns.")
else:
    st.info(
        "Dynamic pricing results are not available. "
        "Run advanced_analytics.py first."
    )


st.markdown("**Pipeline architecture**")
st.code("Cleaned CSV → Hadoop HDFS → MapReduce Word Count\n                         ↘ Apache Spark analytics → spark_results/\n                          ↘ Cassandra (optional persistent storage; connection must be configured)", language="text")
st.caption("The dashboard's interactive charts and recommendations are calculated from the filtered local CSV. HDFS and MapReduce are checked through the Hadoop CLI; Spark is checked for output files; Cassandra is checked only when configured. These checks do not claim an end-to-end streaming pipeline.")

st.divider()
st.caption("StayScope · Airbnb Big Data Analytics · Prices retain the units recorded in the source dataset.")

st.markdown("""
<div style="text-align:center; padding:28px 15px 12px;
            border-top:2px solid #ff385c; margin-top:25px;">
    <p style="font-size:20px; font-weight:600; color:#ff385c;
              font-style:italic; margin-bottom:10px;">
        “The world is full of beautiful places.
        Let data help you find your next stay.”
    </p>
    <p style="font-size:13px; color:#888; letter-spacing:1px;">
        — STAYSCOPE · DISCOVER SMARTER, STAY BETTER
    </p>
</div>
""", unsafe_allow_html=True)
