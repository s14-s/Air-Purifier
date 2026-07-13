import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Air Quality Analyzer", layout="wide")

# Load dataset
@st.cache_data
def load_data():
    df = pd.read_csv("global_air_quality.csv")
    return df

df = load_data()

# Convert date
df["Date"] = pd.to_datetime(df["Date"])

# ---------------- DEFINE POLLUTANTS ----------------
pollutants = ["PM2.5","PM10","NO2","SO2","CO","O3"]

# ---------------- MULTI-POLLUTANT AQI ----------------

def calculate_aqi_pollutant(conc, pollutant):
    """
    conc: pollutant concentration
    pollutant: string, one of 'PM2.5','PM10','NO2','SO2','CO','O3'
    returns: AQI value
    """
    if pollutant == "PM2.5":
        breakpoints = [(0,12,0,50),
                       (12.1,35.4,51,100),
                       (35.5,55.4,101,150),
                       (55.5,150.4,151,200),
                       (150.5,250.4,201,300),
                       (250.5,350.4,301,400),
                       (350.5,500.4,401,500)]
    elif pollutant == "PM10":
        breakpoints = [(0,54,0,50),
                       (55,154,51,100),
                       (155,254,101,150),
                       (255,354,151,200),
                       (355,424,201,300),
                       (425,504,301,400),
                       (505,604,401,500)]
    elif pollutant == "NO2":
        breakpoints = [(0,53,0,50),
                       (54,100,51,100),
                       (101,360,101,150),
                       (361,649,151,200),
                       (650,1249,201,300),
                       (1250,1649,301,400),
                       (1650,2049,401,500)]
    elif pollutant == "SO2":
        breakpoints = [(0,35,0,50),
                       (36,75,51,100),
                       (76,185,101,150),
                       (186,304,151,200),
                       (305,604,201,300),
                       (605,804,301,400),
                       (805,1004,401,500)]
    elif pollutant == "CO":
        breakpoints = [(0,4.4,0,50),
                       (4.5,9.4,51,100),
                       (9.5,12.4,101,150),
                       (12.5,15.4,151,200),
                       (15.5,30.4,201,300),
                       (30.5,40.4,301,400),
                       (40.5,50.4,401,500)]
    elif pollutant == "O3":
        breakpoints = [(0,0.054,0,50),
                       (0.055,0.070,51,100),
                       (0.071,0.085,101,150),
                       (0.086,0.105,151,200),
                       (0.106,0.200,201,300)]
    else:
        return np.nan
    
    for (C_low,C_high,I_low,I_high) in breakpoints:
        if C_low <= conc <= C_high:
            return ((I_high - I_low)/(C_high - C_low))*(conc - C_low) + I_low
    return np.nan

def aqi_category(aqi):
    aqi = round(aqi)
    if aqi >= 0 and aqi <= 50:
        return "Good","green"
    elif aqi >= 51 and aqi <= 100:
        return "Moderate","yellow"
    elif aqi >= 101 and aqi <= 150:
        return "Unhealthy for Sensitive Groups","orange"
    elif aqi >= 151 and aqi <= 200:
        return "Unhealthy","red"
    elif aqi >= 201 and aqi <= 300:
        return "Very Unhealthy","purple"
    else:
        return "Hazardous","maroon"


# Calculate individual AQI for each pollutant
for p in pollutants:
    df[p+"_AQI"] = df[p].apply(lambda x: calculate_aqi_pollutant(x, p))

# Maximum AQI among all pollutants
df["AQI"] = df[[p+"_AQI" for p in pollutants]].max(axis=1)

# Assign risk category and color
df["AQI_Risk"], df["AQI_Color"] = zip(*df["AQI"].apply(aqi_category))


# ---------------- SIDEBAR ----------------

st.sidebar.title("Air Quality Dashboard")

page = st.sidebar.radio(
    "Navigation",
    ["Country Analyzer", "Global Pollution Ranking", "Country Comparison","Global Pollution Map"]
)

# ---------------- PAGE 1 ----------------

if page == "Country Analyzer":

    st.title("Country Air Quality Analyzer")

    country = st.selectbox(
        "Select Country",
        sorted(df["Country"].unique())
    )

    country_df = df[df["Country"] == country]

    # Average pollutant values
    avg_pm25 = country_df["PM2.5"].mean()
    avg_pm10 = country_df["PM10"].mean()
    avg_no2 = country_df["NO2"].mean()
    avg_so2 = country_df["SO2"].mean()
    avg_co = country_df["CO"].mean()
    avg_o3 = country_df["O3"].mean()

    aqi = country_df["AQI"].mean()  # Or median if you prefer
    risk = country_df["AQI_Risk"].iloc[0]
    color = country_df["AQI_Color"].iloc[0]

    # Fix
    aqi = round(country_df["AQI"].mean())  # round the mean AQI
    risk, color = aqi_category(aqi)        # recalculate category after rounding

    st.subheader("Average Pollutant Levels")

    col1,col2,col3 = st.columns(3)
    col4,col5,col6 = st.columns(3)

    col1.metric("PM2.5", round(avg_pm25,2))
    col2.metric("PM10", round(avg_pm10,2))
    col3.metric("NO2", round(avg_no2,2))
    col4.metric("SO2", round(avg_so2,2))
    col5.metric("CO", round(avg_co,2))
    col6.metric("O3", round(avg_o3,2))

    st.subheader("AQI Result")

    st.markdown(
        f"<h1 style='color:{color};'>AQI: {round(aqi)} ({risk})</h1>",
        unsafe_allow_html=True
    )

    # -------- Pollutant Trend --------

    st.subheader("Pollutant Trend Over Time")

    pollutant = st.selectbox(
        "Select Pollutant",
        ["PM2.5","PM10","NO2","SO2","CO","O3"]
    ) 

# Date convert
    country_df["Date"] = pd.to_datetime(country_df["Date"])

# Month column
    country_df["Month"] = country_df["Date"].dt.to_period("M")

# Monthly average pollutant
    monthly_df = country_df.groupby("Month")[pollutant].mean().reset_index()

# Convert month to string
    monthly_df["Month"] = monthly_df["Month"].astype(str)

# Trend calculation
    y = monthly_df[pollutant].values
    x = np.arange(len(y))

# Remove NaNs
    mask = ~np.isnan(y)
    x_clean = x[mask]
    y_clean = y[mask]

# Calculate slope
    slope = np.polyfit(x_clean, y_clean, 1)[0]

# Set a small threshold to avoid misclassification
    threshold = 0.01  # adjust if needed based on your data scale
    if slope > threshold:
        trend = "📈 Increasing Trend"
        trend_color = "red"
    elif slope < -threshold:
        trend = "📉 Decreasing Trend"
        trend_color = "green"
    else:
        trend = "➖ Stable Trend"
        trend_color = "gray" 

    st.markdown(f"<h3 style='color:{trend_color};'>{trend}</h3>", unsafe_allow_html=True)

# Trend graph
    fig = px.line(
        monthly_df,
        x="Month",
        y=pollutant,
        markers=True,
        title=f"{pollutant} Trend in {country}"
    )   

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title=pollutant
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------- Pie Chart --------

    st.subheader("Pollutant Distribution")

    pie_data = pd.DataFrame({
        "Pollutant":["PM2.5","PM10","NO2","SO2","CO","O3"],
        "Value":[avg_pm25,avg_pm10,avg_no2,avg_so2,avg_co,avg_o3]
    })

    pie_chart = px.pie(
        pie_data,
        names="Pollutant",
        values="Value",
        title="Pollutant Composition"
    )

    st.plotly_chart(pie_chart, use_container_width=True)

    st.subheader("Pollutant Correlation Heatmap")

    corr = df[["PM2.5","PM10","NO2","SO2","CO","O3"]].corr()

    fig = px.imshow(
         corr,
         text_auto=True,
         color_continuous_scale=["#e6ccff","#9933ff","#4b0082"],  # light purple → dark purple
         title="Pollutant Correlation Matrix"
    )

    # Increase size
    fig.update_layout(
    height=600
    )

    st.plotly_chart(fig, use_container_width=True,config={"scrollZoom": True})
    


# ---------------- PAGE 2 ----------------

elif page == "Global Pollution Ranking":

    st.title("Global Pollution Ranking (PM2.5 Based)")

    # Average PM2.5 per country
    country_avg = df.groupby("Country").agg({
        "PM2.5": "mean"
    }).reset_index()

    # Use multi-pollutant AQI
    country_avg["AQI"] = df.groupby("Country")["AQI"].mean().values

    # ---------- TOP 10 MOST POLLUTED ----------

    st.subheader("Top 10 Most Polluted Countries (PM2.5)")

    top10 = country_avg.sort_values("PM2.5", ascending=False).head(10)

    fig1 = px.bar(
        top10,
        x="Country",
        y="PM2.5",
        color="PM2.5",
        title="Most Polluted Countries by PM2.5"
    )

    st.plotly_chart(fig1, use_container_width=True)

    st.dataframe(top10)

    # ---------- TOP 10 LEAST POLLUTED ----------

    st.subheader("Top 10 Least Polluted Countries (PM2.5)")

    clean10 = country_avg.sort_values("PM2.5").head(10)

    fig2 = px.bar(
        clean10,
        x="Country",
        y="PM2.5",
        color="PM2.5",
        title="Least Polluted Countries by PM2.5"
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(clean10)

elif page == "Country Comparison":

    st.title("Pollution Comparison Between Countries")

    countries = sorted(df["Country"].unique())

    col1, col2 = st.columns(2)

    with col1:
        country1 = st.selectbox("Select First Country", countries)

    with col2:
        country2 = st.selectbox("Select Second Country", countries)

    data1 = df[df["Country"] == country1]
    data2 = df[df["Country"] == country2]

    # Average pollutants
    avg1 = data1[["PM2.5","PM10","NO2","SO2","CO","O3"]].mean()
    avg2 = data2[["PM2.5","PM10","NO2","SO2","CO","O3"]].mean()

    comparison_df = pd.DataFrame({
        "Pollutant":["PM2.5","PM10","NO2","SO2","CO","O3"],
        country1: avg1.values,
        country2: avg2.values
    })

    st.subheader("Pollutant Level Comparison")

    fig = px.bar(
        comparison_df,
        x="Pollutant",
        y=[country1, country2],
        barmode="group",
        title=f"{country1} vs {country2} Pollution Levels"
    )

    st.plotly_chart(fig, use_container_width=True , config={"scrollZoom": True})
    # -------- AQI COMPARISON --------

    aqi1 = data1["AQI"].mean()
    aqi2 = data2["AQI"].mean()

    st.subheader("AQI Comparison")

    aqi_df = pd.DataFrame({
        "Country":[country1, country2],
        "AQI":[aqi1, aqi2]
    })

    fig = px.bar(
         aqi_df,
         x="Country",
         y="AQI",
         color="Country",
         color_discrete_sequence=["lightblue","darkblue"]  # AQI1 = green, AQI2 = red
    )

    st.plotly_chart(fig, use_container_width=True , config={"scrollZoom": True})

# ---------------- PAGE 3 ----------------
elif page == "Global Pollution Map":

    st.title("Global Air Pollution Map (PM2.5 Based)")

    # Average PM2.5 per country
    country_pm25 = df.groupby("Country")["PM2.5"].mean().reset_index()

    # Country search
    search_country = st.selectbox(
        "Search Country (Optional)",
        ["All Countries"] + sorted(country_pm25["Country"].unique())
    )

    if search_country != "All Countries":
        country_pm25 = country_pm25[country_pm25["Country"] == search_country]

    # Custom pollution color scale
    pollution_scale = [
        [0.0, "green"],
        [0.33, "yellow"],
        [0.66, "orange"],
        [1.0, "darkred"]
    ]

    fig = px.choropleth(
        country_pm25,
        locations="Country",
        locationmode="country names",
        color="PM2.5",
        color_continuous_scale=pollution_scale,
        title="Global PM2.5 Pollution Map"
    )

    fig.update_layout(
        height=750
    )

    st.plotly_chart(fig, use_container_width=True)
    
