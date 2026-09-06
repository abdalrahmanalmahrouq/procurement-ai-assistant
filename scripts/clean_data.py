from pathlib import Path
import re

import pandas as pd


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "PURCHASE ORDER DATA EXTRACT 2012-2015_0.csv"
)

PROCESSED_DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

PROCESSED_DATA_PATH = (
    PROCESSED_DATA_DIR
    / "purchase_orders_cleaned.csv"
)


# ============================================================
# Columns that should remain identifiers / strings
# ============================================================

IDENTIFIER_COLUMNS = [
    "Purchase Order Number",
    "Requisition Number",
    "LPA Number",
    "Supplier Code",
    "Supplier Zip Code",
    "Classification Codes",
    "Normalized UNSPSC",
    "Class",
    "Family",
    "Segment",
]


# ============================================================
# Helper functions
# ============================================================

def normalize_column_name(column_name: str) -> str:
    """
    Convert column names to lowercase snake_case.

    Example:
        Purchase Order Number
        -> purchase_order_number
    """

    column_name = column_name.strip().lower()

    column_name = re.sub(
        r"[^a-z0-9]+",
        "_",
        column_name,
    )

    return column_name.strip("_")


def clean_numeric_column(
    series: pd.Series
) -> pd.Series:
    """
    Convert currency/numeric strings into numeric values.

    Examples:
        "$1,250.50" -> 1250.50
        "1,000"     -> 1000
        "(250.00)"  -> -250.00

    Invalid or empty values become NaN.
    """

    cleaned = (
        series
        .astype("string")
        .str.strip()
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace(
            r"^\((.*)\)$",
            r"-\1",
            regex=True,
        )
    )

    return pd.to_numeric(
        cleaned,
        errors="coerce",
    )


# ============================================================
# Cleaning pipeline
# ============================================================

def clean_data() -> pd.DataFrame:

    print("=" * 60)
    print("California Procurement Data Cleaning")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Validate raw dataset
    # --------------------------------------------------------

    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(
            "\nRaw dataset was not found.\n\n"
            f"Expected location:\n{RAW_DATA_PATH}\n\n"
            "Download the dataset and place the CSV "
            "inside data/raw/."
        )

    print(f"\nReading:\n{RAW_DATA_PATH}")

    # --------------------------------------------------------
    # 2. Preserve identifier columns as strings
    # --------------------------------------------------------

    # Read the header first so we only apply dtypes
    # to columns that actually exist in the CSV.
    header = pd.read_csv(
        RAW_DATA_PATH,
        nrows=0,
    ).columns

    dtype_map = {
        column: "string"
        for column in IDENTIFIER_COLUMNS
        if column in header
    }

    # --------------------------------------------------------
    # 3. Load raw dataset
    # --------------------------------------------------------

    df = pd.read_csv(
        RAW_DATA_PATH,
        dtype=dtype_map,
        low_memory=False,
    )

    print(
        f"\nRaw records loaded: {len(df):,}"
    )

    print(
        f"Raw columns: {len(df.columns)}"
    )

    # --------------------------------------------------------
    # 4. Normalize column names
    # --------------------------------------------------------

    df.columns = [
        normalize_column_name(column)
        for column in df.columns
    ]

    if df.columns.duplicated().any():

        duplicates = (
            df.columns[
                df.columns.duplicated()
            ]
            .tolist()
        )

        raise ValueError(
            "Duplicate columns were created after "
            f"normalization: {duplicates}"
        )

    print(
        "\nColumn names normalized "
        "to lowercase snake_case."
    )

    # --------------------------------------------------------
    # 5. Convert numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "quantity",
        "unit_price",
        "total_price",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = clean_numeric_column(
                df[column]
            )

    print(
        "Numeric columns converted."
    )

    # --------------------------------------------------------
    # 6. Convert date columns
    # --------------------------------------------------------

    date_columns = [
        "creation_date",
        "purchase_date",
    ]

    for column in date_columns:

        if column in df.columns:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
            )

    print(
        "Date columns converted."
    )

    # --------------------------------------------------------
    # 7. Create reconstructed order key
    # --------------------------------------------------------

    required_order_columns = {
        "department_name",
        "purchase_order_number",
        "creation_date",
    }

    missing_columns = (
        required_order_columns
        - set(df.columns)
    )

    if missing_columns:

        raise ValueError(
            "Cannot create order_key. "
            "Missing columns: "
            f"{sorted(missing_columns)}"
        )

    department = (
        df["department_name"]
        .astype("string")
        .fillna("UNKNOWN_DEPARTMENT")
        .str.strip()
    )

    purchase_order = (
        df["purchase_order_number"]
        .astype("string")
        .fillna("UNKNOWN_PO")
        .str.strip()
    )

    creation_date = (
        df["creation_date"]
        .dt.strftime("%Y-%m-%d")
        .fillna("UNKNOWN_DATE")
    )

    df["order_key"] = (
        department
        + "|"
        + purchase_order
        + "|"
        + creation_date
    )

    print(
        "Derived order_key created."
    )

    # --------------------------------------------------------
    # 8. Create time helper fields
    # --------------------------------------------------------

    df["year"] = (
        df["creation_date"]
        .dt.year
        .astype("Int64")
    )

    df["month"] = (
        df["creation_date"]
        .dt.month
        .astype("Int64")
    )

    df["quarter"] = (
        df["creation_date"]
        .dt.quarter
        .astype("Int64")
    )

    print(
        "Derived year, month, and quarter fields created."
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Do NOT:
    # - remove orders below $5,000
    # - remove negative transactions
    # - blindly drop missing rows
    #
    # These values exist in the source dataset and are
    # intentionally preserved for analytical transparency.
    # --------------------------------------------------------

    # --------------------------------------------------------
    # 9. Save processed dataset
    # --------------------------------------------------------

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        PROCESSED_DATA_PATH,
        index=False,
        date_format="%Y-%m-%d",
    )

    # --------------------------------------------------------
    # 10. Cleaning summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("Cleaning Complete")
    print("=" * 60)

    print(
        f"Processed records: {len(df):,}"
    )

    print(
        f"Processed columns: {len(df.columns)}"
    )

    print(
        "Unique reconstructed orders: "
        f"{df['order_key'].nunique():,}"
    )

    if "total_price" in df.columns:

        negative_records = (
            df["total_price"] < 0
        ).sum()

        print(
            "Negative total_price records preserved: "
            f"{negative_records:,}"
        )

    invalid_creation_dates = (
        df["creation_date"].isna().sum()
    )

    print(
        "Missing/unparseable creation dates: "
        f"{invalid_creation_dates:,}"
    )

    print(
        f"\nSaved cleaned dataset to:\n"
        f"{PROCESSED_DATA_PATH}"
    )

    return df


# ============================================================
# Script entry point
# ============================================================

if __name__ == "__main__":
    clean_data()