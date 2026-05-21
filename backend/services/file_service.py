"""
File Service — read CSV / Excel files into a pandas DataFrame.
"""
import pandas as pd
from pathlib import Path


def read_file_to_dataframe(file_path: str, extension: str) -> pd.DataFrame:
    """
    Read a CSV or Excel file into a pandas DataFrame.

    Args:
        file_path: Absolute path to the file on disk.
        extension: File extension (e.g. '.csv', '.xlsx', '.xls').

    Returns:
        pandas DataFrame with the file contents.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = extension.lower()

    if ext == ".csv":
        # Try UTF-8 first, then fall back to latin-1
        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
        except UnicodeDecodeError:
            df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="latin-1")
    elif ext == ".xlsx":
        df = pd.read_excel(path, dtype=str, keep_default_na=False, engine="openpyxl")
    elif ext == ".xls":
        df = pd.read_excel(path, dtype=str, keep_default_na=False, engine="xlrd")
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    # Strip whitespace from column names
    df.columns = [str(c).strip() for c in df.columns]

    return df
