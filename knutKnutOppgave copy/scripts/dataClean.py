import numpy
import pandas
from datetime import datetime

CURRENT_YEAR = datetime.now().year

NUMERIC_COLUMNS = [
    "price", "size", "bathrooms", "kitchens", "storage_rating", "condition_rating",
    "days_on_marked", "sun_factor", "lot_w", "external_storage_m2", "year", "remodeled"
]

REQUIRED_COLUMNS = ["price", "size", "year"]

def clean_data(df):
    # Standardize column names to lowercase early
    df.columns = [col.lower() for col in df.columns]

    # Fix common typo in column name
    if "sold_in_moth" in df.columns and "sold_in_month" not in df.columns:
        df.rename(columns={"sold_in_moth": "sold_in_month"}, inplace=True)

    # Strip whitespace from string columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()

    # Treat certain placeholder values as missing
    df.replace({"": numpy.nan, "unknown": numpy.nan, "None": numpy.nan, "nan": numpy.nan}, inplace=True)

    # Coerce known numeric columns
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pandas.to_numeric(df[col], errors="coerce")

    # Remove rows missing essential fields only
    present_required = [c for c in REQUIRED_COLUMNS if c in df.columns]
    if present_required:
        df = df.dropna(subset=present_required)

    # Remove duplicate rows
    df = df.drop_duplicates()

    # BUSINESS RULE: Drop rows where sold == "no" but sold_in_month has a value (inconsistent)
    if "sold" in df.columns and "sold_in_month" in df.columns:
        inconsistent_mask = (df["sold"].str.lower() == "no") & (df["sold_in_month"].astype(str).str.len() > 0)
        df = df[~inconsistent_mask]

    # Optionally also drop rows where sold == "yes" but sold_in_month missing
    if "sold" in df.columns and "sold_in_month" in df.columns:
        missing_month_mask = (df["sold"].str.lower() == "yes") & (df["sold_in_month"].astype(str).str.len() == 0)
        df = df[~missing_month_mask]

    # Remove impossible / illogical numeric values
    if "price" in df.columns:
        df = df[df["price"] >= 0]
    if "size" in df.columns:
        df = df[df["size"] > 0]
    if "year" in df.columns:
        df = df[(df["year"] >= 1800) & (df["year"] <= CURRENT_YEAR)]
    if "remodeled" in df.columns and "year" in df.columns:
        df = df[(df["remodeled"] >= df["year"]) & (df["remodeled"] <= CURRENT_YEAR)]
    if "sun_factor" in df.columns:
        df = df[(df["sun_factor"] >= 0) & (df["sun_factor"] <= 1)]
    if "days_on_marked" in df.columns:
        df = df[df["days_on_marked"] >= 0]
    if "bathrooms" in df.columns:
        df = df[df["bathrooms"] >= 0]
    if "kitchens" in df.columns:
        df = df[df["kitchens"] >= 0]

    # Ensure integer-like columns are cast to int (after filtering)
    for col in ["bathrooms", "kitchens", "storage_rating", "condition_rating", "year", "remodeled", "lot_w", "external_storage_m2"]:
        if col in df.columns:
            # Only cast if values are not NaN
            df[col] = df[col].astype(int)

    return df

# Path adjusted relative to this script's location
DATA_PATH = "data/houses.jsonl"
OUTPUT_PATH = "data/houses_cleaned.jsonl"

if __name__ == "__main__":
    # Read JSON Lines
    df = pandas.read_json(DATA_PATH, lines=True)
    cleaned_df = clean_data(df)
    # Save cleaned data
    cleaned_df.to_json(OUTPUT_PATH, orient="records", lines=True)
    # Show a brief preview
    print("Cleaned rows:", len(cleaned_df))
    print(cleaned_df.head())
