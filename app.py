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
st.caption("Interactive evaluation dashboard based on DWLR observations")

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
    st.error("Dashboard data files could not be loaded.")
    st.code(str(e))
    st.info(
        "Make sure these CSV files are in the same GitHub repository folder as app.py: "
        "district_dashboard.csv, station_dashboard.csv, monthly_dashboard.csv, "
        "station_monthly_dashboard.csv, evaluation_summary.csv"
    )
    st.stop()

def clean_numeric(df, cols):
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out

station = clean_numeric(
    station,
    ["Observations", "Average_Groundwater", "Minimum_Groundwater",
     "Maximum_Groundwater", "Range", "Latitude", "Longitude"]
)
district = clean_numeric(
    district,
    ["Observations", "Stations", "Average_Groundwater",
     "Minimum_Groundwater", "Maximum_Groundwater", "Range"]
)
monthly = clean_numeric(monthly, ["Average_Groundwater", "Observations"])
station_monthly = clean_numeric(station_monthly, ["Average_Groundwater", "Observations"])

# ---------------- Sidebar filters ----------------
st.sidebar.header("🔎 Filters")

states = sorted(station["State"].dropna().astype(str).unique()) if "State" in station.columns else []
selected_state = st.sidebar.selectbox("State", ["All"] + states)

filtered_station = station.copy()
if selected_state != "All":
    filtered_station = filtered_station[filtered_station["State"].astype(str) == selected_state]

districts = sorted(filtered_station["District"].dropna().astype(str).unique()) if "District" in filtered_station.columns else []
selected_district = st.sidebar.selectbox("District", ["All"] + districts)

if selected_district != "All":
    filtered_station = filtered_station[
        filtered_station["District"].astype(str) == selected_district
    ]

stations = sorted(filtered_station["Station"].dropna().astype(str).unique()) if "Station" in filtered_station.columns else []
selected_station = st.sidebar.selectbox("Station", ["All"] + stations)

if selected_station != "All":
    filtered_station = filtered_station[
        filtered_station["Station"].astype(str) == selected_station
    ]

# ---------------- Overview ----------------
st.header("1. Overview")

c1, c2, c3, c4 = st.columns(4)

total_obs = int(filtered_station["Observations"].fillna(0).sum()) if "Observations" in filtered_station else 0
total_stations = len(filtered_station)

if "District" in filtered_station.columns:
    total_districts = filtered_station["District"].nunique()
else:
    total_districts = 0

weights = filtered_station["Observations"].fillna(0)
values = filtered_station["Average_Groundwater"]
valid = values.notna() & weights.notna() & (weights > 0)
weighted_average = np.average(values[valid], weights=weights[valid]) if valid.any() else np.nan

c1.metric("Valid Observations", f"{total_obs:,}")
c2.metric("Stations", f"{total_stations:,}")
c3.metric("Districts", f"{total_districts:,}")
c4.metric(
    "Average Reported Groundwater",
    f"{weighted_average:.2f}" if pd.notna(weighted_average) else "N/A"
)

st.info(
    "Interpretation note: groundwater values are reported according to the DWLR dataset's "
    "measurement convention. Trend direction should be interpreted together with that convention."
)

# ---------------- Temporal evaluation ----------------
st.header("2. Temporal Evaluation")

trend_data = monthly.copy()

if selected_state != "All" and "State" in trend_data.columns:
    trend_data = trend_data[trend_data["State"].astype(str) == selected_state]
if selected_district != "All" and "District" in trend_data.columns:
    trend_data = trend_data[trend_data["District"].astype(str) == selected_district]

if selected_station != "All":
    if "Station" in station_monthly.columns:
        trend_data = station_monthly[
            station_monthly["Station"].astype(str) == selected_station
        ].copy()

date_col = None
for candidate in ["Month", "Date", "month", "date"]:
    if candidate in trend_data.columns:
        date_col = candidate
        break

if date_col:
    trend_data[date_col] = pd.to_datetime(trend_data[date_col], errors="coerce")
    trend_data = trend_data.dropna(subset=[date_col]).sort_values(date_col)

if len(trend_data) >= 2 and "Average_Groundwater" in trend_data.columns:
    y = pd.to_numeric(trend_data["Average_Groundwater"], errors="coerce").to_numpy()
    x = np.arange(len(y))
    valid_y = ~np.isnan(y)

    if valid_y.sum() >= 2:
        slope = float(np.polyfit(x[valid_y], y[valid_y], 1)[0])
        direction = "Increasing" if slope > 0 else "Decreasing" if slope < 0 else "Stable"
    else:
        slope = np.nan
        direction = "Insufficient data"

    tc1, tc2 = st.columns(2)
    tc1.metric("Trend slope", f"{slope:.4f}" if pd.notna(slope) else "N/A")
    tc2.metric("Statistical direction", direction)

    if date_col:
        fig = px.line(
            trend_data,
            x=date_col,
            y="Average_Groundwater",
            markers=True,
            title="Monthly Average Reported Groundwater"
        )
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Not enough valid monthly data for a trend evaluation.")

# ---------------- District evaluation ----------------
st.header("3. District Evaluation")

district_view = district.copy()

if selected_state != "All" and "State" in district_view.columns:
    district_view = district_view[district_view["State"].astype(str) == selected_state]
if selected_district != "All" and "District" in district_view.columns:
    district_view = district_view[district_view["District"].astype(str) == selected_district]

if len(district_view):
    cols = [
        c for c in [
            "State", "District", "Observations", "Stations",
            "Average_Groundwater", "Minimum_Groundwater",
            "Maximum_Groundwater", "Range"
        ] if c in district_view.columns
    ]
    st.dataframe(district_view[cols], use_container_width=True, hide_index=True)

    if selected_district == "All" and "District" in district_view.columns:
        chart_df = district_view.sort_values("Average_Groundwater").tail(20)
        if len(chart_df):
            fig_d = px.bar(
                chart_df,
                x="District",
                y="Average_Groundwater",
                title="District Average Reported Groundwater"
            )
            fig_d.update_layout(height=450, xaxis_tickangle=-45)
            st.plotly_chart(fig_d, use_container_width=True)
else:
    st.warning("No district data matches the selected filters.")

# ---------------- Station evaluation ----------------
st.header("4. Station Evaluation")

if len(filtered_station):
    cols = [
        c for c in [
            "State", "District", "Station", "Observations",
            "Average_Groundwater", "Minimum_Groundwater",
            "Maximum_Groundwater", "Range"
        ] if c in filtered_station.columns
    ]
    st.dataframe(filtered_station[cols], use_container_width=True, hide_index=True)

    if selected_station != "All" and "Station" in station_monthly.columns:
        sm = station_monthly[
            station_monthly["Station"].astype(str) == selected_station
        ].copy()

        sm_date = next(
            (c for c in ["Month", "Date", "month", "date"] if c in sm.columns),
            None
        )

        if sm_date:
            sm[sm_date] = pd.to_datetime(sm[sm_date], errors="coerce")
            sm = sm.dropna(subset=[sm_date]).sort_values(sm_date)

        if len(sm) and sm_date and "Average_Groundwater" in sm.columns:
            fig_s = px.line(
                sm,
                x=sm_date,
                y="Average_Groundwater",
                markers=True,
                title=f"Monthly Trend — {selected_station}"
            )
            fig_s.update_layout(height=450)
            st.plotly_chart(fig_s, use_container_width=True)
else:
    st.warning("No station data matches the selected filters.")

# ---------------- Spatial evaluation ----------------
st.header("5. Spatial Evaluation")

map_data = filtered_station.copy()

if "Latitude" in map_data.columns and "Longitude" in map_data.columns:
    map_data["Latitude"] = pd.to_numeric(map_data["Latitude"], errors="coerce")
    map_data["Longitude"] = pd.to_numeric(map_data["Longitude"], errors="coerce")

    map_data = map_data.dropna(subset=["Latitude", "Longitude"])
    map_data = map_data[
        map_data["Latitude"].between(-90, 90)
        & map_data["Longitude"].between(-180, 180)
    ]

    if len(map_data):
        hover_cols = [
            c for c in [
                "State", "District", "Average_Groundwater",
                "Minimum_Groundwater", "Maximum_Groundwater"
            ] if c in map_data.columns
        ]

        # Uses Plotly's built-in geographic projection.
        # No st.map() and no Mapbox token are required.
        fig_map = px.scatter_geo(
            map_data,
            lat="Latitude",
            lon="Longitude",
            hover_name="Station" if "Station" in map_data.columns else None,
            hover_data=hover_cols,
            projection="natural earth",
            title="DWLR Station Locations"
        )
        fig_map.update_geos(
            showland=True,
            showcountries=True,
            showcoastlines=True
        )
        fig_map.update_layout(height=600)
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No valid latitude/longitude values are available.")
else:
    st.warning("Latitude and Longitude columns are not available in station data.")

# ---------------- Evaluation summary ----------------
st.header("6. Evaluation Summary")

if len(evaluation):
    st.dataframe(evaluation, use_container_width=True, hide_index=True)
else:
    st.warning("Evaluation summary is empty.")

# ---------------- Data quality ----------------
st.header("7. Data Quality")

quality_cols = st.columns(3)

if "Observations" in station.columns:
    quality_cols[0].metric(
        "Station records evaluated",
        f"{len(station):,}"
    )

if "Average_Groundwater" in station.columns:
    extreme_count = int(
        (
            (station["Average_Groundwater"] < -100)
            | (station["Average_Groundwater"] > 50)
        ).sum()
    )
    quality_cols[1].metric("Extreme flagged station values", f"{extreme_count:,}")

if "Observations" in monthly.columns:
    quality_cols[2].metric(
        "Monthly records",
        f"{len(monthly):,}"
    )

st.caption(
    "Extreme values are flagged for evaluation and are not automatically deleted."
)

# ---------------- Methodology ----------------
st.header("8. Methodology")

st.markdown("""
- DWLR observations are aggregated at station, district, and monthly levels.
- Descriptive statistics include observation count, average, minimum, maximum, and range.
- Monthly trend is evaluated using a simple linear slope.
- Positive slope indicates an increasing statistical trend in the reported values; negative slope indicates a decreasing statistical trend.
- Extreme observations are flagged rather than automatically removed.
- Spatial evaluation uses available station latitude and longitude.
""")

st.header("9. Limitations")

st.markdown("""
1. A statistical trend does not by itself establish the physical cause of groundwater change.
2. The physical meaning of increasing/decreasing groundwater values depends on the dataset's measurement convention.
3. Extreme values may represent genuine field conditions, sensor behavior, or data-quality issues and therefore require contextual validation.
4. Spatial coverage is limited to the DWLR stations represented in the supplied dataset.
""")

st.success("Dashboard loaded successfully.")
