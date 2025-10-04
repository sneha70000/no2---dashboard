import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

# 🔧 API Key for OpenWeatherMap
api_key = "98283a46857999151f99bedfac80ac8a"  # Replace with your actual key

# 🌍 Page setup
st.set_page_config(page_title="NO₂ Pollution Dashboard", layout="wide")

# 🎨 Custom Styling
st.markdown("""
    <style>
    /* Gradient background */
    .stApp {
        background: linear-gradient(to right, #e0f7fa, #fce4ec);
        font-family: 'Segoe UI', sans-serif;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8bbd0;
    }

    /* Main content container */
    .block-container {
        padding: 2rem;
        background-color: rgba(255, 255, 255, 0.85);
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* Headings */
    h1, h2, h3, h4 {
        color: #2c3e50;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# 🏷️ Title
st.title("NO₂ Pollution Dashboard – India (Jan 2023)")

try:
    # 📥 Load CSV
    df = pd.read_csv("NO2_India_Jan2023.csv", sep=",")

    # ✅ Validate and clean data
    expected_cols = ['latitude', 'longitude', 'NO2_column_number_density']
    if not all(col in df.columns for col in expected_cols):
        raise KeyError("CSV must contain columns: latitude, longitude, NO2_column_number_density")

    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['NO2_column_number_density'] = pd.to_numeric(df['NO2_column_number_density'], errors='coerce')
    df.dropna(subset=expected_cols, inplace=True)

    # 🎚️ NO₂ Level Filter
    min_no2 = float(df['NO2_column_number_density'].min())
    max_no2 = float(df['NO2_column_number_density'].max())

    no2_range = st.slider(
        "🎚️ Filter by NO₂ concentration (µg/m³)",
        min_value=min_no2,
        max_value=max_no2,
        value=(min_no2, max_no2)
    )

    # Filter the DataFrame
    filtered_df = df[
        (df['NO2_column_number_density'] >= no2_range[0]) &
        (df['NO2_column_number_density'] <= no2_range[1])
    ]

    # 📊 Sidebar summary
    st.sidebar.header("📊 Summary")
    st.sidebar.write(f"Total Records: {len(df)}")
    st.sidebar.write(f"Max NO₂: {max_no2}")
    st.sidebar.write(f"Min NO₂: {min_no2}")

    # 🧾 Data preview
    st.subheader("📄 Data Sample")
    st.dataframe(filtered_df)

    st.subheader("📈 Data Summary")
    st.write(filtered_df.describe())

    # 🗺️ NO₂ Map (Filtered)
    st.subheader("🗺️ NO₂ Concentration Map")
    m = folium.Map(location=[22.0, 78.0], zoom_start=5)
    for _, row in filtered_df.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=row['NO2_column_number_density'] * 3,
            color='red',
            fill=True,
            fill_opacity=0.6,
            popup=f"NO₂: {row['NO2_column_number_density']}"
        ).add_to(m)

    st_folium(m, width=700, height=500)

    # 🌐 Forecast Search Section
    st.subheader("📡 TEMPO Air Quality Forecast")
    st.markdown("Enter a location to view live air quality forecasts.")

    location_input = st.text_input("📍 Enter your city or coordinates")

    def get_aqi_label(aqi):
        labels = {
            1: "🟢 Good",
            2: "🟡 Fair",
            3: "🟠 Moderate",
            4: "🔴 Poor",
            5: "🟣 Very Poor"
        }
        return labels.get(aqi, "⚪ Unknown")

    if st.button("🔍 Get Forecast"):
        if location_input.strip() == "":
            st.warning("⚠️ Please enter a valid location.")
        else:
            try:
                # Step 1: Get coordinates
                geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location_input}&limit=1&appid={api_key}"
                geo_response = requests.get(geo_url).json()
                if not geo_response:
                    st.error("❌ Location not found. Try a different city.")
                else:
                    lat = geo_response[0]['lat']
                    lon = geo_response[0]['lon']

                    # Step 2: Get forecast
                    forecast_url = f"http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={lat}&lon={lon}&appid={api_key}"
                    forecast_response = requests.get(forecast_url).json()

                    st.success(f"✅ Forecast for '{location_input}' (Lat: {lat}, Lon: {lon}):")

                    for entry in forecast_response['list'][:5]:  # Show first 5 forecast hours
                        dt = pd.to_datetime(entry['dt'], unit='s')
                        aqi = entry['main']['aqi']
                        components = entry['components']
                        label = get_aqi_label(aqi)

                        # 🎨 Color based on AQI
                        color_map = {
                            1: "#d4f4dd",  # Green
                            2: "#fff9c4",  # Yellow
                            3: "#ffe0b2",  # Orange
                            4: "#ffcdd2",  # Red
                            5: "#e1bee7"   # Purple
                        }
                        bg_color = color_map.get(aqi, "#eeeeee")

                        st.markdown(f"""
                        <div style="background-color:{bg_color}; padding:15px; border-radius:10px; margin-bottom:10px">
                            <h4>🕒 {dt.strftime('%Y-%m-%d %H:%M')}</h4>
                            <b>AQI Level:</b> {label}<br>
                            <b>🌬️ NO₂:</b> {components['no2']} µg/m³<br>
                            <b>🌫️ PM2.5:</b> {components['pm2_5']} µg/m³<br>
                            <b>🌈 O₃:</b> {components['o3']} µg/m³<br>
                            <b>🔥 CO:</b> {components['co']} µg/m³<br>
                            <b>🌋 SO₂:</b> {components['so2']} µg/m³
                        </div>
                        """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Error fetching forecast: {e}")

except FileNotFoundError:
    st.error("❌ File not found: Please make sure 'NO2_India_Jan2023.csv' is in the same folder.")
except pd.errors.EmptyDataError:
    st.error("❌ CSV file is empty or corrupted.")
except KeyError as e:
    st.error(f"❌ Missing column: {e}")
except Exception as e:
    st.error(f"❌ Unexpected error: {e}")