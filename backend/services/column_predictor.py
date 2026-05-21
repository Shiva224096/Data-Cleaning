"""
Column Predictor Service — uses the ML classifier to predict column types.
"""
import pandas as pd
from ml.column_classifier import ColumnClassifier


_classifier = ColumnClassifier()


def predict_column_types(df: pd.DataFrame) -> list[dict]:
    """
    Predict the semantic type of each column in the DataFrame.

    Returns:
        List of dicts with keys: column_name, predicted_type, confidence, alternatives
    """
    predictions = []
    for col in df.columns:
        result = _classifier.predict(df[col], col)
        predictions.append(result)
    return predictions
