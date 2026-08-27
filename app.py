import streamlit as st
import pandas as pd
from src.chatbot import ask_chatbot

from src.data_loader import load_data

from src.analytics import (
    prepare_data,
    calculate_kpis,
    seasonal_analysis,
    negative_price_analysis,
    price_capture_analysis,
    source_generation,
    price_condition_analysis,
    peak_demand_analysis,
    solar_wind_analysis,
    daily_analysis,
    hourly_profile,
    negative_price_by_season
)

from src.charts import (
    generation_mix_chart,
    source_chart,
    seasonal_chart,
    price_chart,
    renewable_share_chart,
    duck_curve_chart,
    negative_price_chart,
    price_condition_chart,
    peak_demand_chart,
    heatmap_chart
)


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="GridLens DE",
    page_icon="",
    layout="wide"
)


# ============================================================
# LOAD AND PREPARE DATA
# ============================================================

df = load_data()
df = prepare_data(df)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚡ GridLens DE")

st.sidebar.markdown(
    "German Electricity Market Intelligence"
)

st.sidebar.divider()

min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)


# Apply date filter
if len(date_range) == 2:

    start_date = pd.Timestamp(
        date_range[0]
    )

    end_date = (
        pd.Timestamp(date_range[1])
        + pd.Timedelta(days=1)
    )

    filtered_df = df[
        (df["timestamp"] >= start_date)
        &
        (df["timestamp"] < end_date)
    ].copy()

else:

    filtered_df = df.copy()


# ============================================================
# HEADER
# ============================================================

st.title("⚡ GridLens DE")

st.subheader(
    "German Electricity Market Intelligence"
)

st.caption(
    f"SMARD hourly data • "
    f"{filtered_df['timestamp'].min().date()} → "
    f"{filtered_df['timestamp'].max().date()}"
)


# ============================================================
# KPI SECTION
# ============================================================

st.header("Grid Overview")

kpis = calculate_kpis(filtered_df)


col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        "Average Price",
        f"€{kpis['average_price']:.2f}/MWh"
    )


with col2:

    st.metric(
        "Average Demand",
        f"{kpis['average_demand']:,.0f} MW"
    )


with col3:

    st.metric(
        "Peak Demand",
        f"{kpis['peak_demand']:,.0f} MW"
    )


with col4:

    st.metric(
        "Renewable Share",
        f"{kpis['renewable_share']:.1f}%"
    )


with col5:

    st.metric(
        "Negative Price Hours",
        f"{kpis['negative_price_hours']:,}"
    )


st.divider()


# ============================================================
# GENERATION MIX
# ============================================================

st.header("1. Generation Mix")


col1, col2 = st.columns(2)


with col1:

    renewable_avg = (
        filtered_df["renewable_mw"].mean()
    )

    fossil_avg = (
        filtered_df["fossil_mw"].mean()
    )

    fig = generation_mix_chart(
        renewable_avg,
        fossil_avg
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    source_table = source_generation(
        filtered_df
    )

    fig = source_chart(
        source_table
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


st.subheader("Generation Source Ranking")

st.dataframe(
    source_table.round(2),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# DAILY MARKET CONDITIONS
# ============================================================

st.header("2. Market Trends")

daily = daily_analysis(
    filtered_df
)


col1, col2 = st.columns(2)


with col1:

    st.plotly_chart(
        price_chart(daily),
        use_container_width=True
    )


with col2:

    st.plotly_chart(
        renewable_share_chart(daily),
        use_container_width=True
    )


# ============================================================
# SEASONAL ANALYSIS
# ============================================================

st.header("3. Seasonal Energy Analysis")

seasonal = seasonal_analysis(
    filtered_df
)


st.plotly_chart(
    seasonal_chart(seasonal),
    use_container_width=True
)


st.subheader(
    "Seasonal Performance"
)

st.dataframe(
    seasonal.round(2),
    use_container_width=True,
    hide_index=True
)


# Find strongest seasons
if len(seasonal) > 0:

    highest_renewable = seasonal.loc[
        seasonal["renewable_share"].idxmax()
    ]

    lowest_price = seasonal.loc[
        seasonal["price"].idxmin()
    ]

    st.info(
        f"Highest renewable share: "
        f"**{highest_renewable['season']}** "
        f"({highest_renewable['renewable_share']:.1f}%).  "
        f"Lowest average electricity price: "
        f"**{lowest_price['season']}** "
        f"(€{lowest_price['price']:.2f}/MWh)."
    )


# ============================================================
# SOLAR AND WIND
# ============================================================

st.header(
    "4. Solar & Wind Complementarity"
)


correlation = solar_wind_analysis(
    filtered_df
)


col1, col2 = st.columns(2)


with col1:

    scatter_data = filtered_df.sample(
        min(3000, len(filtered_df)),
        random_state=42
    )

    import plotly.express as px

    fig = px.scatter(
        scatter_data,
        x="solar_mw",
        y="wind_onshore_mw",
        opacity=0.4,
        title="Solar vs Onshore Wind"
    )

    fig.update_xaxes(
        title="Solar Generation (MW)"
    )

    fig.update_yaxes(
        title="Onshore Wind (MW)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with col2:

    st.subheader("Correlation Matrix")

    st.dataframe(
        correlation.round(3),
        use_container_width=True
    )

    solar_wind_corr = correlation.loc[
        "solar_mw",
        "wind_onshore_mw"
    ]

    st.metric(
        "Solar ↔ Onshore Wind",
        f"{solar_wind_corr:.3f}"
    )


# ============================================================
# NEGATIVE PRICE ANALYSIS
# ============================================================

st.header(
    "5. Negative Electricity Prices"
)


negative = negative_price_analysis(
    filtered_df
)


st.dataframe(
    negative.round(2),
    use_container_width=True,
    hide_index=True
)


negative_season = negative_price_by_season(
    filtered_df
)


if len(negative_season) > 0:

    st.plotly_chart(
        negative_price_chart(
            negative_season
        ),
        use_container_width=True
    )


# Explain negative prices
negative_hours = (
    filtered_df["negative_price"].sum()
)


if negative_hours > 0:

    negative_avg_renewables = (
        filtered_df.loc[
            filtered_df["negative_price"],
            "renewable_mw"
        ].mean()
    )

    normal_avg_renewables = (
        filtered_df.loc[
            ~filtered_df["negative_price"],
            "renewable_mw"
        ].mean()
    )

    st.info(
        f"There were **{negative_hours:,} negative-price "
        f"hours** in the selected period. "
        f"Average renewable generation during those "
        f"hours was **{negative_avg_renewables:,.0f} MW**, "
        f"compared with **{normal_avg_renewables:,.0f} MW** "
        f"during non-negative-price hours."
    )


# ============================================================
# PRICE EFFECTIVENESS
# ============================================================

st.header(
    "6. Renewable Price Effectiveness"
)


capture = price_capture_analysis(
    filtered_df
)


if len(capture) > 0:

    capture_chart = px.bar(
        capture.sort_values(
            "capture_ratio"
        ),
        x="capture_ratio",
        y="source",
        orientation="h",
        title="Renewable Price Capture Ratio"
    )

    capture_chart.add_vline(
        x=1,
        line_dash="dash"
    )

    st.plotly_chart(
        capture_chart,
        use_container_width=True
    )


    st.dataframe(
        capture.round(3),
        use_container_width=True,
        hide_index=True
    )


    best = capture.loc[
        capture["capture_ratio"].idxmax()
    ]

    weakest = capture.loc[
        capture["capture_ratio"].idxmin()
    ]

    st.info(
        f"Highest price capture: **{best['source']}** "
        f"({best['capture_ratio']:.2f}). "
        f"Weakest price capture: **{weakest['source']}** "
        f"({weakest['capture_ratio']:.2f})."
    )


# ============================================================
# PEAK DEMAND
# ============================================================

st.header(
    "7. Peak Demand Analysis"
)


peak = peak_demand_analysis(
    filtered_df
)


st.dataframe(
    peak.round(2),
    use_container_width=True,
    hide_index=True
)


st.plotly_chart(
    peak_demand_chart(peak),
    use_container_width=True
)


# ============================================================
# PRICE CONDITIONS
# ============================================================

st.header(
    "8. Low vs High Price Conditions"
)


price_conditions = price_condition_analysis(
    filtered_df
)


st.dataframe(
    price_conditions.round(2),
    use_container_width=True,
    hide_index=True
)


st.plotly_chart(
    price_condition_chart(price_conditions),
    use_container_width=True
)


# ============================================================
# DUCK CURVE
# ============================================================

st.header(
    "9. Duck Curve"
)

st.caption(
    "Average hourly demand, solar generation "
    "and demand after solar."
)


hourly = hourly_profile(
    filtered_df
)


st.plotly_chart(
    duck_curve_chart(hourly),
    use_container_width=True
)


# ============================================================
# PRICE HEATMAP
# ============================================================

st.header(
    "10. Electricity Price Heatmap"
)


heatmap_data = filtered_df.copy()

heatmap_data["date"] = (
    heatmap_data["timestamp"].dt.date
)


price_heatmap = heatmap_data.pivot_table(
    index="date",
    columns="hour",
    values="price_eur_mwh",
    aggfunc="mean"
)


st.plotly_chart(
    heatmap_chart(price_heatmap),
    use_container_width=True
)


# ============================================================
# KEY FINDINGS
# ============================================================

st.header(
    "11. Key Findings"
)


findings_col1, findings_col2 = st.columns(2)


with findings_col1:

    strongest_renewable_season = (
        seasonal.loc[
            seasonal["renewable_share"].idxmax(),
            "season"
        ]
    )

    strongest_solar_season = (
        seasonal.loc[
            seasonal["solar"].idxmax(),
            "season"
        ]
    )

    st.write(
        f" **Strongest renewable season:** "
        f"{strongest_renewable_season}"
    )

    st.write(
        f" **Strongest solar season:** "
        f"{strongest_solar_season}"
    )


with findings_col2:

    strongest_wind_season = (
        seasonal.loc[
            (
                seasonal["wind_onshore"]
                + seasonal["wind_offshore"]
            ).idxmax(),
            "season"
        ]
    )

    lowest_price_season = (
        seasonal.loc[
            seasonal["price"].idxmin(),
            "season"
        ]
    )

    st.write(
        f" **Strongest wind season:** "
        f"{strongest_wind_season}"
    )

    st.write(
        f" **Lowest-price season:** "
        f"{lowest_price_season}"
    )

# ============================================================
# AI CHATBOT
# ============================================================

st.header(" Ask GridLens")

st.caption(
    "Ask questions about the German electricity-market data."
)


# Create a compact context from our actual calculations

# ============================================================
# CHATBOT CONTEXT
# ============================================================

# Seasonal analysis
seasonal_chat = seasonal_analysis(
    filtered_df
)

# Price conditions
price_conditions_chat = price_condition_analysis(
    filtered_df
)

# Price capture
capture_chat = price_capture_analysis(
    filtered_df
)

# Peak demand
peak_chat = peak_demand_analysis(
    filtered_df
)

# Solar/wind correlation
correlation_chat = solar_wind_analysis(
    filtered_df
)

# Negative prices by season
negative_season_chat = negative_price_by_season(
    filtered_df
)


chat_context = f"""

========================
DATASET
========================

Hourly observations:
{len(filtered_df):,}

Period:
{filtered_df["timestamp"].min()} to
{filtered_df["timestamp"].max()}


========================
MARKET
========================

Average electricity price:
€{filtered_df["price_eur_mwh"].mean():.2f}/MWh

Minimum electricity price:
€{filtered_df["price_eur_mwh"].min():.2f}/MWh

Maximum electricity price:
€{filtered_df["price_eur_mwh"].max():.2f}/MWh

Negative-price hours:
{int(filtered_df["negative_price"].sum())}


========================
DEMAND
========================

Average demand:
{filtered_df["consumption_mw"].mean():,.0f} MW

Peak demand:
{filtered_df["consumption_mw"].max():,.0f} MW


========================
GENERATION
========================

Average renewable generation:
{filtered_df["renewable_mw"].mean():,.0f} MW

Average fossil generation:
{filtered_df["fossil_mw"].mean():,.0f} MW

Average renewable generation share:
{filtered_df["renewable_generation_share_pct"].mean():.1f}%


========================
SEASONAL ANALYSIS
========================

{seasonal_chat.to_string(index=False)}


========================
NEGATIVE PRICE BY SEASON
========================

{negative_season_chat.to_string(index=False)}


========================
PRICE CONDITIONS
========================

{price_conditions_chat.to_string(index=False)}


========================
RENEWABLE PRICE CAPTURE
========================

{capture_chat.to_string(index=False)}


========================
PEAK DEMAND
========================

{peak_chat.to_string(index=False)}


========================
SOLAR / WIND CORRELATION
========================

{correlation_chat.to_string()}


========================
GENERAL CORRELATION
========================

Renewable generation vs electricity price:
{
    filtered_df[
        ["renewable_mw", "price_eur_mwh"]
    ].corr().loc[
        "renewable_mw",
        "price_eur_mwh"
    ]
:.3f}
"""


# Chat history
if "messages" not in st.session_state:

    st.session_state.messages = []


# Show previous messages
for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# User input
question = st.chat_input(
    "Ask about the German electricity market..."
)


if question:

    # Show user message
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):

        st.markdown(question)


    # Get answer
    with st.chat_message("assistant"):

        with st.spinner(
            "Analyzing the dataset..."
        ):

            answer = ask_chatbot(
                question,
                chat_context
            )

        st.markdown(answer)


    # Save answer
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

# ============================================================
# DATA EXPLORER
# ============================================================

st.header(
    "12. Data Explorer"
)


display_columns = [
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
        display_columns
    ].tail(100),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "GridLens DE | SMARD data | "
    "Python + Pandas + Plotly + Streamlit"
)