import pandas as pd

from utils.data_loader import load_data


def get_grouped_summary(
    group_by,
    metric="Revenue",
    aggregation="sum",
    filter_column=None,
    filter_value=None
):
    df = load_data()
# Apply an optional filter
    if filter_column is not None:
        df = filter_data(filter_column, filter_value)
    # Check that the requested grouping column exists
    if group_by not in df.columns:
        raise ValueError(f"Unknown grouping column: {group_by}")

    # Check that the requested metric exists
    if metric not in df.columns:
        raise ValueError(f"Unknown metric column: {metric}")

    # Perform the grouping and aggregation
    result = (
        df.groupby(group_by)[metric]
        .agg(aggregation)
        .reset_index()
        .sort_values(metric, ascending=False)
        .reset_index(drop=True)
    )
    

    return result
def get_top_n(group_by, metric="Revenue", n=5):
    """
    Return the top N groups based on an aggregated metric.
    """

    result = get_grouped_summary(
        group_by=group_by,
        metric=metric,
        aggregation="sum"
    )

    return result.head(n)   
def filter_data(column, value):
    """
    Filter the dataset using an exact value match.
    """

    df = load_data()

    # Check that the requested column exists
    if column not in df.columns:
        raise ValueError(f"Unknown column: {column}")

    # Filter rows where the column matches the requested value
    filtered_df = df[df[column] == value].copy()

    return filtered_df

def get_monthly_summary(metric="Revenue", aggregation="sum"):
    """
    Calculate a metric month by month.
    """

    df = load_data()

    # Create a month column
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    # Group by month
    result = (
        df.groupby("Month")[metric]
        .agg(aggregation)
        .reset_index()
        .sort_values("Month")
        .reset_index(drop=True)
    )

    return result