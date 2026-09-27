import plotly.express as px


def create_monthly_chart(df, metric="Revenue"):
    """
    Create an interactive monthly trend chart.
    """

    fig = px.line(
        df,
        x="Month",
        y=metric,
        markers=True,
        title=f"Monthly {metric} Trend"
    )

    return fig