import streamlit as st
from streamlit_folium import folium_static
import folium
import altair as alt
import pandas as pd
import numpy as np
import datetime
from datetime import datetime
from dwdweather import DwdWeather
from folium import plugins

st.beta_set_page_config(page_title="DWD Stations")


@st.cache
def find_close_stations(dist: int = 50, res="hourly"):
    "Find closest stations (dist: radius in km)"

    ifu = (47.476111, 11.062777)

    mapper = {"10min": "10_minutes", "hourly": "hourly", "daily": "daily"}

    dwd = DwdWeather(resolution=mapper[res])
    closest = dwd.nearest_station(lat=ifu[0], lon=ifu[1], surrounding=dist * 1000)
    return closest


# @st.cache
def fetch_data(res="hourly"):

    ifu = (47.476111, 11.062777)

    mapper = {"10min": "10_minutes", "hourly": "hourly", "daily": "daily"}

    # Create client object.
    dwd = DwdWeather(resolution=mapper[res])

    # Find closest station to position.
    closest = dwd.nearest_station(lat=ifu[0], lon=ifu[1])

    st.write(closest)

    # The hour you're interested in.
    # The example is 2014-03-22 12:00 (UTC).
    query_hour = datetime(2014, 3, 22, 12, 10)

    result = dwd.query(station_id=closest["station_id"], timestamp=query_hour)
    return result


st.write("# DWD stations near IMK-IFU/ KIT 🏔🌦")

res = st.sidebar.selectbox("Data resolution", ["10min", "hourly", "daily"])

dist = st.sidebar.slider(
    "Distance to IFU [km]", min_value=10, max_value=150, value=50, step=5
)
closest_stations = find_close_stations(dist=dist, res=res)


@st.cache
def compute_center_coordinate(stations):
    lat = np.array([x["geo_lat"] for x in stations]).mean()
    lon = np.array([x["geo_lon"] for x in stations]).mean()
    return float(lat), float(lon)


@st.cache
def compute_bounds(stations):
    min_lat = np.array([x["geo_lat"] for x in stations]).min()
    min_lon = np.array([x["geo_lon"] for x in stations]).min()
    max_lat = np.array([x["geo_lat"] for x in stations]).max()
    max_lon = np.array([x["geo_lon"] for x in stations]).max()
    return [[float(min_lat), float(min_lon)], [float(max_lat), float(max_lon)]]


@st.cache
def create_chart(df):
    "Create (dummy) charts for popup items"
    chart = alt.Chart(df).mark_line().encode(x="a", y="b").properties(height=100)
    return chart.to_json()


def filter_by_dates(stations, start, end):
    filtered = []
    for station in stations:
        start_date = datetime.strptime(str(station["date_start"]), "%Y%m%d")
        if start_date.day != 1 or start_date.month != 1:
            start_year = start_date.year + 1
        else:
            start_year = start_date.year

        end_date = datetime.strptime(str(station["date_end"]), "%Y%m%d")
        end_year = end_date.year

        if start_year <= start and end_year >= end:
            filtered.append(station)
    return filtered


years = st.sidebar.slider("Data coverage [year]", 1990, 2020, (2010, 2019))
closest_stations = filter_by_dates(closest_stations, *years)

st.write(f"Number of stations: {len(closest_stations)}")

# get data
# data = fetch_data()
# print(data)

ifu = (47.476180, 11.063350)
icon_url = "https://www.kit-ausbildung.de/typo3conf/ext/dp_contentelements/Resources/Public/img/kit-logo-without-text.svg"
icon = folium.features.CustomIcon(icon_url, icon_size=(32, 32))

# center on IFU (Campus Alpin)
m = folium.Map(location=compute_center_coordinate(closest_stations), tiles=None)
folium.TileLayer("Stamen Toner", name="Stamen Toner").add_to(m)
folium.TileLayer("Stamen Terrain", name="Stamen Terrain").add_to(m)
folium.TileLayer("Stamen Watercolor", name="Stamen Watercolor").add_to(m)
folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)

feature_group_tereno = folium.FeatureGroup("TERENO Sites")
feature_group_dwd = folium.FeatureGroup("DWD Sites", control=False)


# add marker for ifu
info = """<b>KIT Campus Alpin</b></br>
<center>
<img src="https://www.imk-ifu.kit.edu/img/gesamtansicht_IFU.gif" width="100px"/>
</center>
"""
info_popup = info + '<a href="https://www.imk-ifu.kit.edu" target="_blank">Homepage</a>'

folium.Marker(ifu, tooltip=info, popup=info_popup, icon=icon).add_to(m)


# tereno stations
tereno_stations = [
    {"name": "Fendth", "geo_lat": 47.83243, "geo_lon": 11.06111},
    {"name": "Grasswang", "geo_lat": 47.57026, "geo_lon": 11.03189},
    {"name": "Rottenbuch", "geo_lat": 47.73032, "geo_lon": 11.03189},
]

for station in tereno_stations:
    folium.Marker(
        (station["geo_lat"], station["geo_lon"]),
        tooltip=f"{station['name']} (TERENO)",
        icon=folium.Icon(color="green", icon="info-sign"),
    ).add_to(feature_group_tereno)

# dwd stations
for station in closest_stations:

    dummy_df = pd.DataFrame(
        {"a": range(100), "b": np.cumsum(np.random.normal(0, 0.1, 100))}
    )

    folium.Marker(
        (station["geo_lat"], station["geo_lon"]),
        tooltip=f"{station['name']} (id:{station['station_id']})",
        # popup = f"{station['name']} (id:{station['station_id']})",
        popup=folium.Popup(max_width=300).add_child(
            folium.VegaLite(create_chart(dummy_df), width=300, height=100)
        ),
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(feature_group_dwd)


# distance circle
folium.Circle(radius=dist * 1000, location=ifu, color="crimson", fill=False).add_to(m)


# fit bounds
bounds = compute_bounds(closest_stations)
m.fit_bounds(bounds)

feature_group_tereno.add_to(m)
feature_group_dwd.add_to(m)
folium.LayerControl(collapsed=True).add_to(m)

plugins.Fullscreen(
    position="topright",
    title="Expand me",
    title_cancel="Exit me",
    force_separate_button=True,
).add_to(m)

# call to render Folium map in Streamlit
folium_static(m)
