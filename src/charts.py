import pandas as pd
import plotly.express as px


def generation_mix_chart(
    renewable,
    fossil
):

    data = pd.DataFrame({
        "Type": [
            "Renewable",
            "Fossil"
        ],
        "MW": [
            renewable,
            fossil
        ]
    })

    fig = px.pie(
        data,
        names="Type",
        values="MW",
        title="Renewable vs Fossil Generation"
    )

    return fig


def source_chart(source_table):

    fig = px.bar(
        source_table,
        x="Average MW",
        y="Source",
        orientation="h",
        title="Average Generation by Source"
    )

    return fig


def price_chart(daily_df):

    fig = px.line(
        daily_df,
        x="date",
        y="average_price",
        title="Daily Average Electricity Price"
    )

    return fig


def renewable_share_chart(daily_df):

    fig = px.line(
        daily_df,
        x="date",
        y="renewable_share",
        title="Daily Renewable Share"
    )

    return fig


def seasonal_chart(seasonal_df):

    fig = px.bar(
        seasonal_df,
        x="season",
        y=[
            "renewable",
            "fossil"
        ],
        barmode="group",
        title="Renewable vs Fossil by Season"
    )

    return fig


def duck_curve_chart(hourly_df):

    fig = px.line(
        hourly_df,
        x="hour",
        y=[
            "demand",
            "net_demand",
            "solar"
        ],
        title="Average Daily Duck Curve"
    )

    return fig


def negative_price_chart(df):

    fig = px.bar(
        df,
        x="season",
        y="negative_hours",
        title="Negative-Price Hours by Season"
    )

    return fig


def price_condition_chart(df):

    fig = px.bar(
        df,
        x="price_condition",
        y=[
            "renewable_generation",
            "fossil_generation"
        ],
        barmode="group",
        title="Generation During Price Conditions"
    )

    return fig


def peak_demand_chart(df):

    fig = px.bar(
        df,
        x="demand_condition",
        y=[
            "renewable",
            "fossil"
        ],
        barmode="group",
        title="Generation During Demand Conditions"
    )

    return fig


def heatmap_chart(price_heatmap):

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
        title="German Electricity Price Heatmap"
    )

    return fig