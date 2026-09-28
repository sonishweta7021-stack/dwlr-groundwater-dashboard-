import streamlit as st
import pandas as pd
import plotly.express as px
import os

# -------------------------------------------------
# PAGE SETTINGS
# -------------------------------------------------

st.set_page_config(
    page_title="DWLR Groundwater Dashboard",
    page_icon="💧",
    layout="wide"
)

# -------------------------------------------------
# TITLE
# -------------------------------------------------

st.title("💧 DWLR Groundwater Level Dashboard")
st.caption(
    "Groundwater monitoring dashboard based on DWLR observations"
)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

@st.cache_data
def load_data():

    district = pd.read_csv(
        "district_dashboard.csv"
    )

    station = pd.read_csv(
        "station_dashboard.csv"
    )

    monthly = pd.read_csv(
        "monthly_dashboard.csv"
    )

    station_monthly = pd.read_csv(
        "station_monthly_dashboard.csv"
    )

    return district, station, monthly, station_monthly


district_df, station_df, monthly_df, station_monthly_df = load_data()

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------

st.sidebar.header("🔎 Filters")

# State filter
states = sorted(
    station_df["State"].dropna().unique()
)

selected_state = st.sidebar.selectbox(
    "Select State",
    ["All"] + states
)

# Apply state filter
if selected_state != "All":

    filtered_station = station_df[
        station_df["State"] == selected_state
    ]

    filtered_district = district_df[
        district_df["State"] == selected_state
    ]

    filtered_monthly = monthly_df[
        monthly_df["State"] == selected_state
    ]

    filtered_station_monthly = station_monthly_df[
        station_monthly_df["State"] == selected_state
    ]

else:

    filtered_station = station_df.copy()
    filtered_district = district_df.copy()
    filtered_monthly = monthly_df.copy()
    filtered_station_monthly = station_monthly_df.copy()


# -------------------------------------------------
# DISTRICT FILTER
# -------------------------------------------------

districts = sorted(
    filtered_station["District"]
    .dropna()
    .unique()
)

selected_district = st.sidebar.selectbox(
    "Select District",
    ["All"] + districts
)

if selected_district != "All":

    filtered_station = filtered_station[
        filtered_station["District"] == selected_district
    ]

    filtered_district = filtered_district[
        filtered_district["District"] == selected_district
    ]

    filtered_monthly = filtered_monthly[
        filtered_monthly["District"] == selected_district
    ]

    filtered_station_monthly = filtered_station_monthly[
        filtered_station_monthly["District"] == selected_district
    ]


# -------------------------------------------------
# STATION FILTER
# -------------------------------------------------

stations = sorted(
    filtered_station["Station"]
    .dropna()
    .unique()
)

selected_station = st.sidebar.selectbox(
    "Select Station",
    ["All"] + stations
)

if selected_station != "All":

    filtered_station = filtered_station[
        filtered_station["Station"] == selected_station
    ]

    filtered_station_monthly = filtered_station_monthly[
        filtered_station_monthly["Station"] == selected_station
    ]


# -------------------------------------------------
# DASHBOARD METRICS
# -------------------------------------------------

total_observations = int(
    filtered_station["Observations"].sum()
)

total_stations = filtered_station["Station"].nunique()

total_districts = filtered_station["District"].nunique()

if len(filtered_station) > 0:

    average_groundwater = (
        filtered_station["Average_Groundwater"]
        .mean()
    )

else:

    average_groundwater = 0


# -------------------------------------------------
# METRIC CARDS
# -------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "📊 Observations",
    f"{total_observations:,}"
)

col2.metric(
    "📍 Stations",
    f"{total_stations:,}"
)

col3.metric(
    "🏘️ Districts",
    f"{total_districts:,}"
)

col4.metric(
    "💧 Average Groundwater",
    f"{average_groundwater:.2f}"
)


st.divider()


# -------------------------------------------------
# MONTHLY TREND
# -------------------------------------------------

st.subheader("📈 Groundwater Level Trend")

if len(filtered_monthly) > 0:

    trend_df = (
        filtered_monthly
        .groupby("Month", as_index=False)
        ["Average_Groundwater"]
        .mean()
        .sort_values("Month")
    )

    fig = px.line(
        trend_df,
        x="Month",
        y="Average_Groundwater",
        markers=True,
        title="Monthly Average Groundwater Level"
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Average Groundwater Level"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.info("No monthly data available for this selection.")


# -------------------------------------------------
# DISTRICT SUMMARY
# -------------------------------------------------

st.subheader("🏘️ District Summary")

if len(filtered_district) > 0:

    district_chart = (
        filtered_district
        .groupby("District", as_index=False)
        ["Average_Groundwater"]
        .mean()
        .sort_values(
            "Average_Groundwater"
        )
    )

    fig2 = px.bar(
        district_chart,
        x="District",
        y="Average_Groundwater",
        title="Average Groundwater Level by District"
    )

    fig2.update_layout(
        xaxis_title="District",
        yaxis_title="Average Groundwater Level"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

else:

    st.info("No district data available.")


# -------------------------------------------------
# STATION TREND
# -------------------------------------------------

st.subheader("📍 Station-wise Monthly Trend")

if selected_station != "All":

    station_trend = (
        filtered_station_monthly
        .sort_values("Month")
    )

    if len(station_trend) > 0:

        fig3 = px.line(
            station_trend,
            x="Month",
            y="Average_Groundwater",
            markers=True,
            title=f"Monthly Groundwater — {selected_station}"
        )

        fig3.update_layout(
            xaxis_title="Month",
            yaxis_title="Average Groundwater Level"
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

    else:

        st.info(
            "No monthly station data available."
        )

else:

    st.info(
        "Select a station from the sidebar "
        "to view its monthly trend."
    )


# -------------------------------------------------
# STATION MAP
# -------------------------------------------------

st.subheader("🗺️ DWLR Station Map")

map_df = filtered_station[
    [
        "Station",
        "Latitude",
        "Longitude"
    ]
].dropna()

map_df = map_df.rename(
    columns={
        "Latitude": "latitude",
        "Longitude": "longitude"
    }
)

# Keep only valid coordinates
map_df = map_df[
    (map_df["latitude"].between(-90, 90)) &
    (map_df["longitude"].between(-180, 180))
]

if len(map_df) > 0:

    st.map(
        map_df[
            ["latitude", "longitude"]
        ]
    )

else:

    st.info(
        "No valid station coordinates available."
    )


# -------------------------------------------------
# STATION TABLE
# -------------------------------------------------

st.subheader("📋 Station Information")

display_station = filtered_station[
    [
        "State",
        "District",
        "Station",
        "Observations",
        "Average_Groundwater",
        "Minimum_Groundwater",
        "Maximum_Groundwater",
        "Latitude",
        "Longitude"
    ]
].copy()

st.dataframe(
    display_station,
    use_container_width=True,
    hide_index=True
)


# -------------------------------------------------
# FOOTER
# -------------------------------------------------

st.divider()

st.caption(
    "DWLR Groundwater Monitoring Project | "
    "Interactive Data Dashboard"
  )
