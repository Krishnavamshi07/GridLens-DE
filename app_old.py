import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="GridLens DE",
    page_icon="⚡",
    layout="wide"
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():
    df = pd.read_parquet(
        "data/processed/final_analytics_data.parquet"
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df


df = load_data()


# ============================================================
# PREPARE DATA
# ============================================================

# Time features
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour
df["month"] = df["timestamp"].dt.month
df["month_name"] = df["timestamp"].dt.month_name()
df["day_of_week"] = df["timestamp"].dt.day_name()


# Seasons
def get_season(month):
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:
        return "Autumn"


df["season"] = df["month"].apply(get_season)


# Renewable and fossil groups
renewable_columns = [
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
    "biomass_mw",
    "hydro_mw",
    "other_renewables_mw"
]

fossil_columns = [
    "gas_mw",
    "coal_mw",
    "lignite_mw"
]

df["renewable_mw"] = df[renewable_columns].sum(axis=1)

df["fossil_mw"] = df[fossil_columns].sum(axis=1)

df["listed_generation_mw"] = (
    df["renewable_mw"] +
    df["fossil_mw"]
)

df["renewable_generation_share_pct"] = (
    df["renewable_mw"] /
    df["listed_generation_mw"] *
    100
)


# Other metrics
df["negative_price"] = df["price_eur_mwh"] < 0

df["net_demand_mw"] = (
    df["consumption_mw"] -
    df["solar_mw"]
)

# Peak demand = top 10%
peak_threshold = df["consumption_mw"].quantile(0.90)

df["peak_demand"] = (
    df["consumption_mw"] >= peak_threshold
)


# ============================================================
# HEADER
# ============================================================

st.title("⚡ GridLens DE")

st.markdown(
    "### German Electricity Market Intelligence"
)

st.caption(
    "Hourly analysis of electricity demand, generation mix, "
    "renewables and market prices."
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Dashboard Filters")

min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:

    start_date = pd.Timestamp(date_range[0])
    end_date = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)

    filtered_df = df[
        (df["timestamp"] >= start_date) &
        (df["timestamp"] < end_date)
    ].copy()

else:
    filtered_df = df.copy()


# ============================================================
# TOP KPIs
# ============================================================

average_price = filtered_df["price_eur_mwh"].mean()

average_demand = filtered_df["consumption_mw"].mean()

peak_demand = filtered_df["consumption_mw"].max()

average_renewable_share = (
    filtered_df["renewable_generation_share_pct"].mean()
)

negative_price_hours = (
    filtered_df["negative_price"].sum()
)

renewable_average = filtered_df["renewable_mw"].mean()

fossil_average = filtered_df["fossil_mw"].mean()


# ============================================================
# KPI CARDS
# ============================================================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Avg Price",
        f"€{average_price:.2f}/MWh"
    )

with col2:
    st.metric(
        "Avg Demand",
        f"{average_demand:,.0f} MW"
    )

with col3:
    st.metric(
        "Peak Demand",
        f"{peak_demand:,.0f} MW"
    )

with col4:
    st.metric(
        "Renewable Share",
        f"{average_renewable_share:.1f}%"
    )

with col5:
    st.metric(
        "Negative Price Hours",
        f"{negative_price_hours:,}"
    )


st.divider()


# ============================================================
# OVERVIEW
# ============================================================

st.header("1. Generation & Market Overview")

col1, col2 = st.columns(2)


# Generation mix
with col1:

    mix_data = pd.DataFrame({
        "Type": [
            "Renewable",
            "Fossil"
        ],
        "Average MW": [
            renewable_average,
            fossil_average
        ]
    })

    fig = px.pie(
        mix_data,
        names="Type",
        values="Average MW",
        title="Renewable vs Fossil Generation"
    )

    fig.update_traces(
        textinfo="percent+label"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# Source ranking
with col2:

    source_data = {
        "Solar": "solar_mw",
        "Wind Onshore": "wind_onshore_mw",
        "Wind Offshore": "wind_offshore_mw",
        "Biomass": "biomass_mw",
        "Hydro": "hydro_mw",
        "Gas": "gas_mw",
        "Coal": "coal_mw",
        "Lignite": "lignite_mw"
    }

    source_table = []

    for source, column in source_data.items():
        source_table.append({
            "Source": source,
            "Average MW": filtered_df[column].mean()
        })

    source_table = pd.DataFrame(
        source_table
    ).sort_values(
        "Average MW",
        ascending=True
    )

    fig = px.bar(
        source_table,
        x="Average MW",
        y="Source",
        orientation="h",
        title="Average Generation by Source"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# PRICE + RENEWABLE TREND
# ============================================================

st.header("2. Market Price & Renewable Conditions")

daily = (
    filtered_df
    .groupby("date")
    .agg(
        average_price=("price_eur_mwh", "mean"),
        renewable_generation=("renewable_mw", "mean"),
        renewable_share=("renewable_generation_share_pct", "mean")
    )
    .reset_index()
)

daily["date"] = pd.to_datetime(
    daily["date"]
)


col1, col2 = st.columns(2)


with col1:

    fig = px.line(
        daily,
        x="date",
        y="average_price",
        title="Daily Average Electricity Price"
    )

    fig.update_yaxes(
        title="€ / MWh"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    fig = px.line(
        daily,
        x="date",
        y="renewable_share",
        title="Daily Renewable Generation Share"
    )

    fig.update_yaxes(
        title="%"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# SEASONAL ANALYSIS
# ============================================================

st.header("3. Seasonal Energy Analysis")

season_order = [
    "Winter",
    "Spring",
    "Summer",
    "Autumn"
]

seasonal = (
    filtered_df
    .groupby("season")
    .agg(
        renewable=("renewable_mw", "mean"),
        fossil=("fossil_mw", "mean"),
        renewable_share=(
            "renewable_generation_share_pct",
            "mean"
        ),
        solar=("solar_mw", "mean"),
        wind_onshore=("wind_onshore_mw", "mean"),
        wind_offshore=("wind_offshore_mw", "mean"),
        price=("price_eur_mwh", "mean"),
        demand=("consumption_mw", "mean")
    )
    .reindex(season_order)
    .reset_index()
)


col1, col2 = st.columns(2)


with col1:

    fig = px.bar(
        seasonal,
        x="season",
        y=[
            "renewable",
            "fossil"
        ],
        barmode="group",
        title="Renewable vs Fossil by Season"
    )

    fig.update_yaxes(
        title="Average MW"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    fig = px.bar(
        seasonal,
        x="season",
        y="renewable_share",
        title="Renewable Share by Season"
    )

    fig.update_yaxes(
        title="%"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


st.dataframe(
    seasonal.round(2),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# SOLAR VS WIND
# ============================================================

st.header("4. Solar vs Wind Complementarity")

solar_wind_corr = filtered_df[
    [
        "solar_mw",
        "wind_onshore_mw",
        "wind_offshore_mw"
    ]
].corr()

col1, col2 = st.columns(2)


with col1:

    fig = px.scatter(
        filtered_df.sample(
            min(3000, len(filtered_df)),
            random_state=42
        ),
        x="solar_mw",
        y="wind_onshore_mw",
        opacity=0.4,
        title="Solar vs Onshore Wind"
    )

    fig.update_xaxes(
        title="Solar (MW)"
    )

    fig.update_yaxes(
        title="Onshore Wind (MW)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    st.subheader("Correlation")

    st.dataframe(
        solar_wind_corr.round(3),
        use_container_width=True
    )

    solar_wind_value = solar_wind_corr.loc[
        "solar_mw",
        "wind_onshore_mw"
    ]

    st.write(
        f"Solar vs onshore wind correlation: "
        f"**{solar_wind_value:.3f}**"
    )


# ============================================================
# NEGATIVE PRICE ANALYSIS
# ============================================================

st.header("5. Negative Price Analysis")

negative_df = filtered_df[
    filtered_df["negative_price"]
]

normal_df = filtered_df[
    ~filtered_df["negative_price"]
]

negative_hours = len(negative_df)

if negative_hours > 0:

    comparison = pd.DataFrame({
        "Condition": [
            "Normal Price",
            "Negative Price"
        ],
        "Average Renewable MW": [
            normal_df["renewable_mw"].mean(),
            negative_df["renewable_mw"].mean()
        ],
        "Average Renewable Share %": [
            normal_df[
                "renewable_generation_share_pct"
            ].mean(),
            negative_df[
                "renewable_generation_share_pct"
            ].mean()
        ],
        "Average Demand MW": [
            normal_df["consumption_mw"].mean(),
            negative_df["consumption_mw"].mean()
        ],
        "Average Price €/MWh": [
            normal_df["price_eur_mwh"].mean(),
            negative_df["price_eur_mwh"].mean()
        ]
    })

    st.dataframe(
        comparison.round(2),
        use_container_width=True,
        hide_index=True
    )


    negative_by_season = (
        negative_df
        .groupby("season")
        .size()
        .reindex(season_order)
        .fillna(0)
        .reset_index(name="negative_hours")
    )

    fig = px.bar(
        negative_by_season,
        x="season",
        y="negative_hours",
        title="Negative-Price Hours by Season"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.info(
        "No negative-price hours in the selected period."
    )


# ============================================================
# PRICE EFFECTIVENESS
# ============================================================

st.header("6. Renewable Price Effectiveness")

overall_price = filtered_df[
    "price_eur_mwh"
].mean()

capture_results = []

for source in renewable_columns:

    generation = filtered_df[source].sum()

    if generation == 0:
        continue

    weighted_price = (
        (
            filtered_df[source] *
            filtered_df["price_eur_mwh"]
        ).sum()
        /
        generation
    )

    capture_ratio = (
        weighted_price /
        overall_price
    )

    capture_results.append({
        "Source": source.replace(
            "_mw",
            ""
        ).replace(
            "_",
            " "
        ).title(),
        "Weighted Market Price": weighted_price,
        "Capture Ratio": capture_ratio
    })


capture_table = pd.DataFrame(
    capture_results
)

capture_table = capture_table.sort_values(
    "Capture Ratio"
)


fig = px.bar(
    capture_table,
    x="Capture Ratio",
    y="Source",
    orientation="h",
    title="Renewable Price Capture Ratio"
)

fig.add_vline(
    x=1,
    line_dash="dash"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.dataframe(
    capture_table.round(3),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# PEAK DEMAND ANALYSIS
# ============================================================

st.header("7. Peak Demand Conditions")

peak_df = filtered_df[
    filtered_df["peak_demand"]
]

normal_demand_df = filtered_df[
    ~filtered_df["peak_demand"]
]


peak_comparison = pd.DataFrame({
    "Condition": [
        "Normal Demand",
        "Peak Demand"
    ],
    "Average Demand MW": [
        normal_demand_df["consumption_mw"].mean(),
        peak_df["consumption_mw"].mean()
    ],
    "Renewable MW": [
        normal_demand_df["renewable_mw"].mean(),
        peak_df["renewable_mw"].mean()
    ],
    "Fossil MW": [
        normal_demand_df["fossil_mw"].mean(),
        peak_df["fossil_mw"].mean()
    ],
    "Price €/MWh": [
        normal_demand_df["price_eur_mwh"].mean(),
        peak_df["price_eur_mwh"].mean()
    ]
})

st.dataframe(
    peak_comparison.round(2),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# PRICE QUARTILES
# ============================================================

st.header("8. Low-Price vs High-Price Conditions")

quartile_df = filtered_df.copy()

quartile_df["price_group"] = pd.qcut(
    quartile_df["price_eur_mwh"],
    4,
    labels=[
        "Lowest 25%",
        "25–50%",
        "50–75%",
        "Highest 25%"
    ]
)

price_analysis = (
    quartile_df
    .groupby(
        "price_group",
        observed=True
    )
    .agg(
        average_price=("price_eur_mwh", "mean"),
        renewable_generation=("renewable_mw", "mean"),
        renewable_share=(
            "renewable_generation_share_pct",
            "mean"
        ),
        fossil_generation=("fossil_mw", "mean"),
        consumption=("consumption_mw", "mean")
    )
    .reset_index()
)

st.dataframe(
    price_analysis.round(2),
    use_container_width=True,
    hide_index=True
)


fig = px.bar(
    price_analysis,
    x="price_group",
    y=[
        "renewable_generation",
        "fossil_generation"
    ],
    barmode="group",
    title="Generation Conditions Across Price Levels"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# DUCK CURVE
# ============================================================

st.header("9. Duck Curve")

hourly_profile = (
    filtered_df
    .groupby("hour")
    .agg(
        demand=("consumption_mw", "mean"),
        solar=("solar_mw", "mean"),
        net_demand=("net_demand_mw", "mean")
    )
    .reset_index()
)


fig = px.line(
    hourly_profile,
    x="hour",
    y=[
        "demand",
        "net_demand",
        "solar"
    ],
    title="Average Hourly Demand and Solar Impact"
)

fig.update_xaxes(
    title="Hour of Day",
    dtick=1
)

fig.update_yaxes(
    title="MW"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# PRICE HEATMAP
# ============================================================

st.header("10. Electricity Price Heatmap")

heatmap_df = filtered_df.copy()

heatmap_df["date"] = heatmap_df[
    "timestamp"
].dt.date

price_heatmap = heatmap_df.pivot_table(
    index="date",
    columns="hour",
    values="price_eur_mwh",
    aggfunc="mean"
)

fig = px.imshow(
    price_heatmap,
    aspect="auto",
    color_continuous_scale="RdYlGn_r",
    color_continuous_midpoint=0,
    labels={
        "x": "Hour",
        "y": "Date",
        "color": "€/MWh"
    },
    title="Hourly Electricity Price Heatmap"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# KEY INSIGHTS
# ============================================================

st.header("11. Key Findings")

highest_season = seasonal.loc[
    seasonal["renewable_share"].idxmax(),
    "season"
]

lowest_price_season = seasonal.loc[
    seasonal["price"].idxmin(),
    "season"
]

highest_solar_season = seasonal.loc[
    seasonal["solar"].idxmax(),
    "season"
]

highest_wind_season = seasonal.loc[
    (
        seasonal["wind_onshore"] +
        seasonal["wind_offshore"]
    ).idxmax(),
    "season"
]


col1, col2, col3, col4 = st.columns(4)


with col1:
    st.metric(
        "Strongest Renewable Season",
        highest_season
    )

with col2:
    st.metric(
        "Lowest Avg Price Season",
        lowest_price_season
    )

with col3:
    st.metric(
        "Strongest Solar Season",
        highest_solar_season
    )

with col4:
    st.metric(
        "Strongest Wind Season",
        highest_wind_season
    )


st.markdown(
    f"""
### What the data says

**Renewables:** The highest average renewable-generation
share occurs in **{highest_season}**.

**Market price:** The lowest seasonal average electricity
price occurs in **{lowest_price_season}**.

**Solar:** Solar output is highest in **{highest_solar_season}**.

**Wind:** Combined onshore and offshore wind output is
highest in **{highest_wind_season}**.

**Negative prices:** The selected period contains
**{negative_price_hours:,} negative-price hours**.

These findings are calculated directly from the SMARD
hourly dataset rather than being manually entered.
"""
)


# ============================================================
# DATA EXPLORER
# ============================================================

st.header("12. Data Explorer")

show_columns = [
    "timestamp",
    "consumption_mw",
    "renewable_mw",
    "fossil_mw",
    "solar_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "price_eur_mwh"
]

st.dataframe(
    filtered_df[
        show_columns
    ].tail(100),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "GridLens DE • Data source: SMARD • "
    "Built with Python, Pandas, Plotly and Streamlit"
)