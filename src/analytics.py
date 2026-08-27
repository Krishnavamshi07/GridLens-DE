import pandas as pd


RENEWABLE_COLUMNS = [
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
    "biomass_mw",
    "hydro_mw",
    "other_renewables_mw"
]

FOSSIL_COLUMNS = [
    "gas_mw",
    "coal_mw",
    "lignite_mw"
]


def prepare_data(df):

    df = df.copy()

    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["month"] = df["timestamp"].dt.month

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

    df["renewable_mw"] = (
        df[RENEWABLE_COLUMNS].sum(axis=1)
    )

    df["fossil_mw"] = (
        df[FOSSIL_COLUMNS].sum(axis=1)
    )

    df["listed_generation_mw"] = (
        df["renewable_mw"] +
        df["fossil_mw"]
    )

    df["renewable_generation_share_pct"] = (
        df["renewable_mw"]
        / df["listed_generation_mw"]
        * 100
    )

    df["negative_price"] = (
        df["price_eur_mwh"] < 0
    )

    df["net_demand_mw"] = (
        df["consumption_mw"] -
        df["solar_mw"]
    )

    peak_threshold = df[
        "consumption_mw"
    ].quantile(0.90)

    df["peak_demand"] = (
        df["consumption_mw"]
        >= peak_threshold
    )

    return df


def calculate_kpis(df):

    return {
        "average_price": df[
            "price_eur_mwh"
        ].mean(),

        "average_demand": df[
            "consumption_mw"
        ].mean(),

        "peak_demand": df[
            "consumption_mw"
        ].max(),

        "renewable_share": df[
            "renewable_generation_share_pct"
        ].mean(),

        "negative_price_hours": int(
            df["negative_price"].sum()
        )
    }


def source_generation(df):

    sources = {
        "Solar": "solar_mw",
        "Wind Onshore": "wind_onshore_mw",
        "Wind Offshore": "wind_offshore_mw",
        "Biomass": "biomass_mw",
        "Hydro": "hydro_mw",
        "Gas": "gas_mw",
        "Coal": "coal_mw",
        "Lignite": "lignite_mw"
    }

    results = []

    for source, column in sources.items():

        results.append({
            "Source": source,
            "Average MW": df[column].mean()
        })

    return (
        pd.DataFrame(results)
        .sort_values(
            "Average MW",
            ascending=False
        )
    )


def daily_analysis(df):

    result = (
        df.groupby("date")
        .agg(
            average_price=(
                "price_eur_mwh",
                "mean"
            ),
            renewable_generation=(
                "renewable_mw",
                "mean"
            ),
            renewable_share=(
                "renewable_generation_share_pct",
                "mean"
            ),
            demand=(
                "consumption_mw",
                "mean"
            )
        )
        .reset_index()
    )

    result["date"] = pd.to_datetime(
        result["date"]
    )

    return result


def seasonal_analysis(df):

    seasons = [
        "Winter",
        "Spring",
        "Summer",
        "Autumn"
    ]

    result = (
        df.groupby("season")
        .agg(
            renewable=(
                "renewable_mw",
                "mean"
            ),
            fossil=(
                "fossil_mw",
                "mean"
            ),
            renewable_share=(
                "renewable_generation_share_pct",
                "mean"
            ),
            solar=(
                "solar_mw",
                "mean"
            ),
            wind_onshore=(
                "wind_onshore_mw",
                "mean"
            ),
            wind_offshore=(
                "wind_offshore_mw",
                "mean"
            ),
            price=(
                "price_eur_mwh",
                "mean"
            ),
            demand=(
                "consumption_mw",
                "mean"
            )
        )
        .reindex(seasons)
        .reset_index()
    )

    return result


def negative_price_analysis(df):

    result = (
        df.groupby("negative_price")
        .agg(
            average_price=(
                "price_eur_mwh",
                "mean"
            ),
            renewable_generation=(
                "renewable_mw",
                "mean"
            ),
            renewable_share=(
                "renewable_generation_share_pct",
                "mean"
            ),
            demand=(
                "consumption_mw",
                "mean"
            )
        )
        .reset_index()
    )

    return result


def negative_price_by_season(df):

    result = (
        df[df["negative_price"]]
        .groupby("season")
        .size()
        .reset_index(
            name="negative_hours"
        )
    )

    seasons = [
        "Winter",
        "Spring",
        "Summer",
        "Autumn"
    ]

    result["season"] = pd.Categorical(
        result["season"],
        categories=seasons,
        ordered=True
    )

    return result.sort_values("season")


def price_capture_analysis(df):

    overall_price = df[
        "price_eur_mwh"
    ].mean()

    results = []

    for column in RENEWABLE_COLUMNS:

        generation = df[column].sum()

        if generation == 0:
            continue

        weighted_price = (
            (
                df[column] *
                df["price_eur_mwh"]
            ).sum()
            / generation
        )

        capture_ratio = (
            weighted_price /
            overall_price
        )

        results.append({
            "source": column.replace(
                "_mw",
                ""
            ).replace(
                "_",
                " "
            ).title(),

            "weighted_price":
                weighted_price,

            "capture_ratio":
                capture_ratio
        })

    return pd.DataFrame(results)


def price_condition_analysis(df):

    low = df[
        "price_eur_mwh"
    ].quantile(0.10)

    high = df[
        "price_eur_mwh"
    ].quantile(0.90)

    temp = df.copy()

    temp["price_condition"] = "Normal"

    temp.loc[
        temp["price_eur_mwh"] <= low,
        "price_condition"
    ] = "Low Price"

    temp.loc[
        temp["price_eur_mwh"] >= high,
        "price_condition"
    ] = "High Price"

    result = (
        temp.groupby("price_condition")
        .agg(
            average_price=(
                "price_eur_mwh",
                "mean"
            ),
            renewable_generation=(
                "renewable_mw",
                "mean"
            ),
            renewable_share=(
                "renewable_generation_share_pct",
                "mean"
            ),
            fossil_generation=(
                "fossil_mw",
                "mean"
            ),
            consumption=(
                "consumption_mw",
                "mean"
            )
        )
        .reset_index()
    )

    order = [
        "Low Price",
        "Normal",
        "High Price"
    ]

    result["price_condition"] = pd.Categorical(
        result["price_condition"],
        categories=order,
        ordered=True
    )

    return result.sort_values(
        "price_condition"
    )


def peak_demand_analysis(df):

    temp = df.copy()

    threshold = temp[
        "consumption_mw"
    ].quantile(0.90)

    temp["demand_condition"] = (
        "Normal Demand"
    )

    temp.loc[
        temp["consumption_mw"] >= threshold,
        "demand_condition"
    ] = "Peak Demand"

    result = (
        temp.groupby("demand_condition")
        .agg(
            demand=(
                "consumption_mw",
                "mean"
            ),
            renewable=(
                "renewable_mw",
                "mean"
            ),
            fossil=(
                "fossil_mw",
                "mean"
            ),
            price=(
                "price_eur_mwh",
                "mean"
            )
        )
        .reset_index()
    )

    return result


def solar_wind_analysis(df):

    return df[
        [
            "solar_mw",
            "wind_onshore_mw",
            "wind_offshore_mw"
        ]
    ].corr()


def hourly_profile(df):

    return (
        df.groupby("hour")
        .agg(
            demand=(
                "consumption_mw",
                "mean"
            ),
            solar=(
                "solar_mw",
                "mean"
            ),
            net_demand=(
                "net_demand_mw",
                "mean"
            )
        )
        .reset_index()
    )