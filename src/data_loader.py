import pandas as pd


def load_data():
    df = pd.read_parquet(
        "data/processed/final_analytics_data.parquet"
    )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    return df