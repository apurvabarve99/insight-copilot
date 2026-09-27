from pathlib import Path

import pandas as pd


# Find the main project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Location of our dataset
DATA_FILE = PROJECT_ROOT / "data" / "Sales_Dataset_2024.xlsx"


def load_data():
    """
    Load the Global Superstore dataset and prepare it for analysis.
    """

    # Check whether the dataset exists
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {DATA_FILE}"
        )

    # Read the Excel file
    df = pd.read_excel(DATA_FILE)

    # Convert Date column to pandas datetime
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Replace missing categorical values with "Unknown"
    categorical_columns = [
        "Region",
        "Product",
        "Salesperson"
    ]

    for column in categorical_columns:
        df[column] = df[column].fillna("Unknown")
        df[column] = df[column].str.strip()

    # Standardize known Region variations
    region_mapping = {
        "south": "South",
        "north": "North",
        "NORTH": "North",
        "westt": "West",
        "Easst": "East"
    }

    df["Region"] = df["Region"].replace(region_mapping)

    # Standardize known Product variations
    product_mapping = {
        "tabllet": "Tablet",
        "MOBLIE": "Mobile",
        "SMARTWATCH": "Smartwatch",
        "headPhones": "Headphones",
        "laptop": "Laptop"
    }

    df["Product"] = df["Product"].replace(product_mapping)

    return df