from utils.data_loader import load_data


def get_monthly_trend(
    metric="Revenue",
    filter_column=None,
    filter_value=None
):
    """
    Calculate monthly values and month-over-month percentage changes.

    An optional filter can be used to calculate the trend for
    a specific group, such as one product or one region.
    """
    df = load_data()

    # Apply an optional filter
    if filter_column is not None:
        if filter_column not in df.columns:
            raise ValueError(
                f"Unknown filter column: {filter_column}"
            )

        df = df[df[filter_column] == filter_value].copy()

    if metric not in df.columns:
        raise ValueError(
            f"Unknown metric column: {metric}"
        )

    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    result = (
        df.groupby("Month")[metric]
        .sum()
        .reset_index()
        .sort_values("Month")
    )

    result["Percentage_Change"] = result[metric].pct_change() * 100

    return result