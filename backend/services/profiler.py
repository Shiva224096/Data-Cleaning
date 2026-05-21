"""
Profiler Service — generate column-level statistics for a DataFrame.
"""
import numpy as np
import pandas as pd


def profile_dataframe(df: pd.DataFrame) -> list[dict]:
    """
    Generate detailed profile statistics for every column in the DataFrame.

    Returns a list of dicts, one per column, containing:
        - column_name, dtype, total_count, missing_count, missing_pct,
          unique_count, unique_pct, top_values, min, max, mean, median,
          std, sample_values, has_outliers, outlier_count
    """
    profiles: list[dict] = []

    for col in df.columns:
        series = df[col]
        total = len(series)
        missing = series.isin(["", "nan", "None", "NaN", "null", "NULL"]).sum() + series.isna().sum()
        missing_pct = round((missing / total) * 100, 2) if total > 0 else 0.0
        unique = series.nunique()
        unique_pct = round((unique / total) * 100, 2) if total > 0 else 0.0

        # Top 5 most frequent values
        top_vals = (
            series.value_counts()
            .head(5)
            .to_dict()
        )
        # Convert keys to strings for JSON serialization
        top_vals = {str(k): int(v) for k, v in top_vals.items()}

        # Sample values (up to 5 non-empty)
        non_empty = series[~series.isin(["", "nan", "None", "NaN", "null", "NULL"]) & series.notna()]
        samples = non_empty.head(5).tolist()

        col_profile: dict = {
            "column_name": col,
            "dtype": str(series.dtype),
            "total_count": int(total),
            "missing_count": int(missing),
            "missing_pct": missing_pct,
            "unique_count": int(unique),
            "unique_pct": unique_pct,
            "top_values": top_vals,
            "sample_values": samples,
        }

        # Numeric statistics — try to convert
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().sum() > 0:
            col_profile["min"] = float(numeric.min())
            col_profile["max"] = float(numeric.max())
            col_profile["mean"] = round(float(numeric.mean()), 4)
            col_profile["median"] = float(numeric.median())
            col_profile["std"] = round(float(numeric.std()), 4) if numeric.std() is not None else None

            # Outlier detection via IQR
            q1 = numeric.quantile(0.25)
            q3 = numeric.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = ((numeric < lower) | (numeric > upper)) & numeric.notna()
            col_profile["has_outliers"] = bool(outliers.any())
            col_profile["outlier_count"] = int(outliers.sum())
        else:
            col_profile["min"] = None
            col_profile["max"] = None
            col_profile["mean"] = None
            col_profile["median"] = None
            col_profile["std"] = None
            col_profile["has_outliers"] = False
            col_profile["outlier_count"] = 0

        # String length stats for text columns
        str_lengths = series.astype(str).str.len()
        col_profile["avg_length"] = round(float(str_lengths.mean()), 2)
        col_profile["min_length"] = int(str_lengths.min())
        col_profile["max_length"] = int(str_lengths.max())

        profiles.append(col_profile)

    return profiles
