import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="DWLR Groundwater Resource Evaluation",
    page_icon="💧",
    layout="wide"
)

st.title("💧 Real-Life Groundwater Resource Evaluation Using DWLR Data")
st.markdown(
    "**Interactive analysis dashboard for groundwater observations collected through Digital Water Level Recorder (DWLR) stations.**"
)

@st.cache_data
def load_data():
    district = pd.read_csv("district_dashboard.csv")
    station = pd.read_csv("station_dashboard.csv")
    monthly = pd.read_csv("monthly_dashboard.csv")
    station_monthly = pd.read_csv("station_monthly_dashboard.csv")
    evaluation = pd.read_csv("evaluation_summary.csv")
    return district, station, monthly, station_monthly, evaluation

try:
    district, station, monthly, station_monthly, evaluation = load_data()
except Exception as e:
    st.error("❌ Dashboard data could not be loaded.")
    st.write("Check that all five CSV files are in the same GitHub folder as app.py.")
    st.code(
        "district_dashboard.csv\n"
        "station_dashboard.csv\n"
        "monthly_dashboard.csv\n"
        "station_monthly_dashboard.csv\n"
        "evaluation_summary.csv"
    )
    st.exception(e)
    st.stop()

for dataframe in [district, station, monthly, station_monthly, evaluation]:
    for column in ["State", "District", "Station"]:
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].fillna("Unknown")

numeric_columns = [
    "Observations", "Average_Groundwater", "Minimum_Groundwater",
    "Maximum_Groundwater", "Range", "Trend_Slope", "Latitude", "Longitude"
]

for dataframe in [district, station, monthly, station_monthly, evaluation]:
    for column in numeric_columns:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

st.sidebar.header("🔎 Dashboard Filters")

states = sorted(station["State"].dropna().unique().tolist())
selected_state = st.sidebar.selectbox("Select State", ["All States"] + states)

if selected_state == "All States":
    filtered_station_state = station.copy()
    filtered_monthly_state = monthly.copy()
    filtered_evaluation_state = evaluation.copy()
else:
    filtered_station_state = station[station["State"] == selected_state]
    filtered_monthly_state = monthly[monthly["State"] == selected_state]
    filtered_evaluation_state = evaluation[evaluation["State"] == selected_state]

districts = sorted(filtered_station_state["District"].dropna().unique().tolist())
selected_district = st.sidebar.selectbox("Select District", ["All Districts"] + districts)

if selected_district == "All Districts":
    filtered_station_district = filtered_station_state
    filtered_monthly_district = filtered_monthly_state
    filtered_evaluation_district = filtered_evaluation_state
else:
    filtered_station_district = filtered_station_state[
        filtered_station_state["District"] == selected_district
    ]
    filtered_monthly_district = filtered_monthly_state[
        filtered_monthly_state["District"] == selected_district
    ]
    filtered_evaluation_district = filtered_evaluation_state[
        filtered_evaluation_state["District"] == selected_district
    ]

stations = sorted(filtered_station_district["Station"].dropna().unique().tolist())
selected_station = st.sidebar.selectbox("Select DWLR Station", ["All Stations"] + stations)

if selected_station == "All Stations":
    filtered_station = filtered_station_district
    filtered_monthly = filtered_monthly_district
    filtered_evaluation = filtered_evaluation_district
else:
    filtered_station = filtered_station_district[
        filtered_station_district["Station"] == selected_station
    ]
    filtered_monthly = station_monthly[
        (station_monthly["State"] == selected_state)
        & (station_monthly["District"] == selected_district)
        & (station_monthly["Station"] == selected_station)
    ]
    filtered_evaluation = filtered_evaluation_district[
        filtered_evaluation_district["Station"] == selected_station
    ]

st.header("📊 1. Groundwater Resource Overview")

total_observations = int(filtered_station["Observations"].sum()) if len(filtered_station) else 0
total_stations = int(filtered_station["Station"].nunique()) if len(filtered_station) else 0
total_districts = int(filtered_station["District"].nunique()) if len(filtered_station) else 0

if len(filtered_station) > 0 and filtered_station["Observations"].fillna(0).sum() > 0:
    weighted_average = np.average(
        filtered_station["Average_Groundwater"].fillna(0),
        weights=filtered_station["Observations"].fillna(0)
    )
else:
    weighted_average = np.nan

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Observations", f"{total_observations:,}")
with col2:
    st.metric("DWLR Stations", f"{total_stations:,}")
with col3:
    st.metric("Districts", f"{total_districts:,}")
with col4:
    st.metric(
        "Average Reported Level",
        f"{weighted_average:.2f}" if not pd.isna(weighted_average) else "N/A"
    )

st.info(
    "Note: The groundwater values shown here are reported DWLR measurements. "
    "Physical interpretation of increasing or decreasing groundwater level depends "
    "on the measurement convention used by the source dataset."
)

st.header("📈 2. Temporal Groundwater Evaluation")

if len(filtered_monthly) > 0:
    trend_data = filtered_monthly.copy()
    trend_data["Month"] = trend_data["Month"].astype(str)
    trend_data = trend_data.sort_values("Month")

    fig = px.line(
        trend_data,
        x="Month",
        y="Average_Groundwater",
        markers=True,
        title="Monthly Average Reported Groundwater Level"
    )
    fig.update_layout(xaxis_title="Month", yaxis_title="Average Groundwater Level")
    st.plotly_chart(fig, use_container_width=True)

    if len(trend_data) >= 2:
        x = np.arange(len(trend_data))
        y = trend_data["Average_Groundwater"].values
        valid = ~pd.isna(y)
        slope = np.polyfit(x[valid], y[valid], 1)[0] if valid.sum() >= 2 else np.nan
    else:
        slope = np.nan

    if pd.isna(slope):
        direction = "Insufficient data"
    elif slope > 0.05:
        direction = "Increasing"
    elif slope < -0.05:
        direction = "Decreasing"
    else:
        direction = "Relatively stable"

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Trend Slope", f"{slope:.4f}" if not pd.isna(slope) else "N/A")
    with c2:
        st.metric("Trend Direction", direction)
else:
    st.warning("No temporal data available for the selected filters.")

st.header("🏢 3. District-Level Evaluation")

district_view = filtered_station.groupby(
    ["State", "District"], as_index=False
).agg(
    Observations=("Observations", "sum"),
    Stations=("Station", "nunique"),
    Average_Groundwater=("Average_Groundwater", "mean"),
    Minimum_Groundwater=("Minimum_Groundwater", "min"),
    Maximum_Groundwater=("Maximum_Groundwater", "max")
)

if len(district_view) > 0:
    district_view["Range"] = (
        district_view["Maximum_Groundwater"] - district_view["Minimum_Groundwater"]
    )
    st.dataframe(district_view.round(3), use_container_width=True, hide_index=True)

    district_chart = px.bar(
        district_view,
        x="District",
        y="Average_Groundwater",
        title="Average Reported Groundwater Level by District"
    )
    st.plotly_chart(district_chart, use_container_width=True)
else:
    st.warning("No district data available.")

st.header("📍 4. DWLR Station Evaluation")

if selected_station != "All Stations":
    if len(filtered_evaluation) > 0:
        row = filtered_evaluation.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Average", f"{row['Average_Groundwater']:.3f}")
        with c2:
            st.metric("Minimum", f"{row['Minimum_Groundwater']:.3f}")
        with c3:
            st.metric("Maximum", f"{row['Maximum_Groundwater']:.3f}")
        with c4:
            st.metric("Trend", str(row["Trend_Direction"]))

        st.write(
            "**Trend slope:**",
            round(float(row["Trend_Slope"]), 5)
            if not pd.isna(row["Trend_Slope"]) else "N/A"
        )
        st.write(
            "**Observed range:**",
            round(float(row["Range"]), 3)
            if not pd.isna(row["Range"]) else "N/A"
        )

    station_trend = station_monthly[
        (station_monthly["State"] == selected_state)
        & (station_monthly["District"] == selected_district)
        & (station_monthly["Station"] == selected_station)
    ].copy()

    if len(station_trend) > 0:
        station_trend["Month"] = station_trend["Month"].astype(str)
        station_trend = station_trend.sort_values("Month")
        fig_station = px.line(
            station_trend,
            x="Month",
            y="Average_Groundwater",
            markers=True,
            title=f"Monthly Trend — {selected_station}"
        )
        st.plotly_chart(fig_station, use_container_width=True)
else:
    st.info("Select a specific DWLR station from the sidebar to see detailed station evaluation.")

# ============================================================
# SPATIAL EVALUATION - FIXED
# ============================================================

st.header("🗺️ 5. Spatial Evaluation of DWLR Stations")

map_data = filtered_station.copy()

if "Latitude" in map_data.columns and "Longitude" in map_data.columns:
    map_data["Latitude"] = pd.to_numeric(map_data["Latitude"], errors="coerce")
    map_data["Longitude"] = pd.to_numeric(map_data["Longitude"], errors="coerce")

    map_data = map_data.dropna(subset=["Latitude", "Longitude"])

    map_data = map_data[
        (map_data["Latitude"] >= -90)
        & (map_data["Latitude"] <= 90)
        & (map_data["Longitude"] >= -180)
        & (map_data["Longitude"] <= 180)
    ]

    if len(map_data) > 0:
        # Use Plotly Scatter Geo instead of st.map.
        # This avoids Streamlit map API/version compatibility issues.
        hover_columns = [
            col for col in [
                "State",
                "District",
                "Station",
                "Average_Groundwater",
                "Minimum_Groundwater",
                "Maximum_Groundwater"
            ]
            if col in map_data.columns
        ]

        fig_map = px.scatter_geo(
            map_data,
            lat="Latitude",
            lon="Longitude",
            hover_name="Station" if "Station" in map_data.columns else None,
            hover_data=hover_columns,
            title="DWLR Station Locations"
        )

        fig_map.update_geos(
            showcountries=True,
            showland=True,
            fitbounds="locations"
        )

        fig_map.update_layout(
            height=600,
            margin=dict(l=10, r=10, t=60, b=10)
        )

        st.plotly_chart(
            fig_map,
            use_container_width=True
        )

        st.success(
            f"🗺️ {len(map_data)} DWLR station location(s) available on the map."
        )

        st.subheader("📍 Station Location Details")

        location_columns = [
            "State", "District", "Station",
            "Latitude", "Longitude", "Average_Groundwater"
        ]
        location_columns = [
            col for col in location_columns if col in map_data.columns
        ]

        st.dataframe(
            map_data[location_columns].round(4),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning(
            "⚠️ No valid latitude/longitude values are available for the selected filters."
        )
else:
    st.warning(
        "⚠️ Latitude or Longitude columns are not available in station_dashboard.csv."
    )

st.header("📋 6. Station Evaluation Summary")

evaluation_display = filtered_evaluation.copy()

if len(evaluation_display) > 0:
    columns_to_show = [
        "State", "District", "Station", "Observations",
        "Average_Groundwater", "Minimum_Groundwater",
        "Maximum_Groundwater", "Range",
        "Trend_Slope", "Trend_Direction"
    ]
    columns_to_show = [
        col for col in columns_to_show if col in evaluation_display.columns
    ]

    st.dataframe(
        evaluation_display[columns_to_show].round(4),
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("No evaluation records available for the selected filters.")

st.header("⚠️ 7. Data Quality and Preprocessing")

q1, q2, q3 = st.columns(3)
with q1:
    st.metric("Valid Groundwater Observations", "352,488")
with q2:
    st.metric("Extreme Observations Flagged", "2,107")
with q3:
    st.metric("Invalid Date Records", "1")

st.markdown(
    """
### Data-quality interpretation

The preprocessing stage identified extreme groundwater observations and one invalid
date record.

Extreme observations were **flagged rather than automatically deleted**, because
their validity depends on the measurement convention and domain context of the
DWLR dataset.
"""
)

st.header("🔬 8. Evaluation Methodology")
st.markdown(
    """
**Data Collection**  
↓  
**Data Cleaning**  
↓  
**Date Validation**  
↓  
**Missing/Extreme Value Checking**  
↓  
**Station & District Aggregation**  
↓  
**Monthly Aggregation**  
↓  
**Trend Analysis**  
↓  
**Spatial Evaluation**  
↓  
**Interactive Dashboard**
"""
)

st.header("ℹ️ 9. Limitations")
st.markdown(
    """
- Statistical groundwater-level trends do not by themselves establish groundwater-resource sustainability.
- Rainfall, recharge, groundwater extraction, geology and aquifer properties are not fully represented.
- Extreme observations require domain validation.
- Increasing/decreasing reported values should be interpreted according to the measurement convention of the source dataset.
- The dashboard is an analytical visualization system and not a substitute for a complete hydrogeological assessment.
"""
)

st.markdown("---")
st.caption(
    "Real-Life Groundwater Resource Evaluation Using DWLR Data | Interactive Streamlit Dashboard"
)
