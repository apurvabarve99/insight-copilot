from utils.data_loader import load_data


def detect_anomalies(column="Profit"):
    """
    Detect potential anomalies using the IQR method.
    """

    df = load_data()

    values = df[column].dropna()

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)

    iqr = q3 - q1

    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    anomalies = df[
        (df[column] < lower_bound) |
        (df[column] > upper_bound)
    ].copy()

    return anomalies