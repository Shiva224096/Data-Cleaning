"""
ML Column Classifier — predicts column semantic types using a two-stage
approach: fast heuristic regex matching first, then a trained
RandomForest classifier on extracted features.
"""
import re
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


# ─── Heuristic Regex Patterns ────────────────────────────────────────────────

_PATTERNS: dict[str, re.Pattern] = {
    "email": re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"),
    "url": re.compile(r"^(https?://|www\.)\S+", re.IGNORECASE),
    "ip_address": re.compile(r"^(\d{1,3}\.){3}\d{1,3}$|^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$"),
    "phone": re.compile(r"^[\+]?[(]?\d{1,4}[)]?[\s.\-]?\(?\d{1,5}\)?[\s.\-]?\d{1,5}[\s.\-]?\d{1,9}$"),
    "date": re.compile(
        r"^\d{1,4}[/\-\.]\d{1,2}[/\-\.]\d{1,4}$|"
        r"^\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{2,4}$|"
        r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{2,4}$",
        re.IGNORECASE,
    ),
    "uuid": re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"),
    "mac_address": re.compile(r"^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$"),
    "hex_color": re.compile(r"^#?([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$"),
    "pan": re.compile(r"^[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z]$"),
    "gst": re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z][A-Z\d]$"),
    "ssn": re.compile(r"^\d{3}-?\d{2}-?\d{4}$"),
    "zip_code": re.compile(r"^\d{5}(-\d{4})?$|^\d{6}$|^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$"),
    "isbn": re.compile(r"^(97[89])?\d{9}[\dXx]$"),
    "vin": re.compile(r"^[A-HJ-NPR-Z0-9]{17}$"),
}

# Column name hints for each type
_NAME_HINTS: dict[str, list[str]] = {
    "email": ["email", "e-mail", "mail", "email_address", "emailaddress"],
    "phone": ["phone", "mobile", "cell", "telephone", "tel", "fax", "contact_number", "phone_number"],
    "name": ["name", "first_name", "last_name", "full_name", "firstname", "lastname", "fullname",
             "fname", "lname", "person", "contact_name"],
    "company": ["company", "organization", "org", "employer", "firm", "business", "company_name",
                "organisation"],
    "date": ["date", "dob", "birth", "created", "updated", "timestamp", "datetime",
             "start_date", "end_date", "hire_date", "join_date"],
    "number": ["amount", "price", "cost", "quantity", "qty", "total", "salary",
               "revenue", "count", "age", "score", "rate", "id", "num"],
    "url": ["url", "website", "link", "homepage", "web", "site", "href"],
    "ip_address": ["ip", "ip_address", "ipaddress", "server_ip", "client_ip"],
    "financial": ["iban", "credit_card", "card_number", "account_number", "cc"],
    "pan": ["pan", "pan_number", "pan_no"],
    "gst": ["gst", "gst_number", "gstin", "gst_no"],
    "ssn": ["ssn", "social_security", "social_security_number"],
    "uuid": ["uuid", "guid", "id", "identifier"],
    "isbn": ["isbn", "book_id"],
    "vin": ["vin", "vehicle_id", "vehicle_identification"],
    "mac_address": ["mac", "mac_address", "hardware_address"],
    "hex_color": ["color", "colour", "hex_color", "bg_color", "font_color"],
    "zip_code": ["zip", "zipcode", "zip_code", "postal", "postal_code", "postcode", "pincode", "pin"],
    "text": ["description", "comment", "note", "notes", "remarks", "text", "message", "bio",
             "summary", "address", "street", "city", "state", "country"],
}


class ColumnClassifier:
    """
    Two-stage column type classifier:
    1. Heuristic: regex pattern matching + column name hints
    2. ML: RandomForest trained on synthetic feature vectors
    """

    def __init__(self):
        self._type_list = [
            "email", "phone", "name", "company", "date", "number", "url",
            "ip_address", "financial", "pan", "gst", "ssn", "uuid", "isbn",
            "vin", "mac_address", "hex_color", "zip_code", "text",
        ]
        self._model: RandomForestClassifier | None = None
        self._train_model()

    def _train_model(self):
        """
        Train a RandomForest on synthetic feature vectors for each column type.
        Features: [pct_numeric, pct_alpha, pct_special, avg_length, unique_ratio,
                   has_at_sign, has_dot, has_dash, has_plus, has_colon,
                   pct_pattern_email, pct_pattern_phone, pct_pattern_date,
                   pct_pattern_url, pct_pattern_ip, pct_pattern_uuid]
        """
        # Synthetic training data — representative feature vectors for each type
        X_train = []
        y_train = []

        # Each entry: (type, [pct_numeric, pct_alpha, pct_special, avg_length,
        #               unique_ratio, has_at, has_dot, has_dash, has_plus,
        #               has_colon, email_pct, phone_pct, date_pct, url_pct, ip_pct, uuid_pct])
        synthetic = {
            "email":     [(0.15, 0.55, 0.30, 22.0, 0.95, 1.0, 1.0, 0.1, 0.05, 0.0, 0.90, 0.0, 0.0, 0.0, 0.0, 0.0)],
            "phone":     [(0.75, 0.0,  0.25, 12.0, 0.80, 0.0, 0.0, 0.3, 0.3,  0.0, 0.0,  0.85, 0.0, 0.0, 0.0, 0.0)],
            "name":      [(0.0,  0.90, 0.10, 12.0, 0.85, 0.0, 0.1, 0.1, 0.0,  0.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.0)],
            "company":   [(0.05, 0.80, 0.15, 18.0, 0.90, 0.0, 0.2, 0.1, 0.0,  0.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.0)],
            "date":      [(0.55, 0.10, 0.35, 10.0, 0.70, 0.0, 0.1, 0.5, 0.0,  0.0, 0.0,  0.0,  0.80, 0.0, 0.0, 0.0)],
            "number":    [(0.95, 0.0,  0.05, 6.0,  0.60, 0.0, 0.2, 0.05, 0.0, 0.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.0)],
            "url":       [(0.10, 0.50, 0.40, 35.0, 0.95, 0.0, 1.0, 0.3, 0.0,  0.3, 0.0,  0.0,  0.0, 0.90, 0.0, 0.0)],
            "ip_address":[(0.65, 0.0,  0.35, 13.0, 0.80, 0.0, 1.0, 0.0, 0.0,  0.3, 0.0,  0.0,  0.0, 0.0, 0.85, 0.0)],
            "financial": [(0.70, 0.15, 0.15, 20.0, 0.95, 0.0, 0.0, 0.2, 0.0,  0.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.0)],
            "pan":       [(0.40, 0.60, 0.0,  10.0, 0.95, 0.0, 0.0, 0.0, 0.0,  0.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.0)],
            "gst":       [(0.45, 0.50, 0.05, 15.0, 0.95, 0.0, 0.0, 0.0, 0.0,  0.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.0)],
            "ssn":       [(0.75, 0.0,  0.25, 11.0, 0.95, 0.0, 0.0, 1.0, 0.0,  0.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.0)],
            "uuid":      [(0.55, 0.30, 0.15, 36.0, 1.0,  0.0, 0.0, 1.0, 0.0,  0.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.90)],
            "isbn":      [(0.85, 0.0,  0.15, 13.0, 0.95, 0.0, 0.0, 0.5, 0.0,  0.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.0)],
            "vin":       [(0.45, 0.55, 0.0,  17.0, 0.99, 0.0, 0.0, 0.0, 0.0,  0.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.0)],
            "mac_address":[(0.55, 0.30, 0.15, 17.0, 0.95, 0.0, 0.0, 0.0, 0.0,  1.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.0)],
            "hex_color": [(0.40, 0.40, 0.20, 7.0,  0.70, 0.0, 0.0, 0.0, 0.0,  0.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.0)],
            "zip_code":  [(0.90, 0.0,  0.10, 5.5,  0.30, 0.0, 0.0, 0.1, 0.0,  0.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.0)],
            "text":      [(0.05, 0.70, 0.25, 50.0, 0.95, 0.0, 0.3, 0.1, 0.0,  0.0, 0.0,  0.0,  0.0, 0.0, 0.0, 0.0)],
        }

        # Generate multiple noisy samples per type
        rng = np.random.RandomState(42)
        for type_name, templates in synthetic.items():
            label_idx = self._type_list.index(type_name)
            for template in templates:
                for _ in range(50):
                    noise = rng.normal(0, 0.05, len(template))
                    features = np.clip(np.array(template) + noise, 0, 1)
                    # Don't clip avg_length to [0,1] — it can be larger
                    features[3] = max(1.0, template[3] + rng.normal(0, 3))
                    X_train.append(features)
                    y_train.append(label_idx)

        X_train = np.array(X_train)
        y_train = np.array(y_train)

        self._model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
        )
        self._model.fit(X_train, y_train)

    def predict(self, series: pd.Series, column_name: str) -> dict:
        """
        Predict the semantic type of a pandas Series.

        Returns dict with: column_name, predicted_type, confidence, alternatives
        """
        # ── Stage 1: Heuristic (column name matching) ──────────────────────
        col_lower = column_name.lower().replace(" ", "_")
        name_scores: dict[str, float] = {}

        for type_name, hints in _NAME_HINTS.items():
            for hint in hints:
                if col_lower == hint or col_lower.endswith("_" + hint) or col_lower.startswith(hint + "_"):
                    name_scores[type_name] = name_scores.get(type_name, 0) + 0.6
                elif hint in col_lower:
                    name_scores[type_name] = name_scores.get(type_name, 0) + 0.3

        # ── Stage 1b: Heuristic (regex pattern matching on samples) ────────
        non_empty = series[series.astype(str).str.strip().ne("") & series.notna()]
        sample = non_empty.head(100).astype(str)

        pattern_scores: dict[str, float] = {}
        if len(sample) > 0:
            for type_name, pattern in _PATTERNS.items():
                match_count = sample.apply(lambda x: bool(pattern.match(x.strip()))).sum()
                match_pct = match_count / len(sample)
                if match_pct > 0.5:
                    pattern_scores[type_name] = match_pct

        # If heuristics give high confidence, return early
        combined_heuristic = {}
        for t in self._type_list:
            combined_heuristic[t] = name_scores.get(t, 0) * 0.4 + pattern_scores.get(t, 0) * 0.6

        best_heuristic = max(combined_heuristic, key=combined_heuristic.get)
        if combined_heuristic[best_heuristic] > 0.5:
            alternatives = sorted(
                [(t, round(s, 3)) for t, s in combined_heuristic.items() if s > 0.1 and t != best_heuristic],
                key=lambda x: -x[1],
            )[:3]
            return {
                "column_name": column_name,
                "predicted_type": best_heuristic,
                "confidence": round(min(combined_heuristic[best_heuristic], 0.99), 3),
                "method": "heuristic",
                "alternatives": [{"type": t, "score": s} for t, s in alternatives],
            }

        # ── Stage 2: ML Features ──────────────────────────────────────────
        features = self._extract_features(series, sample)
        feature_vector = np.array(features).reshape(1, -1)

        proba = self._model.predict_proba(feature_vector)[0]
        predicted_idx = np.argmax(proba)
        predicted_type = self._type_list[predicted_idx]
        confidence = float(proba[predicted_idx])

        # Combine ML prediction with any name hints
        if name_scores:
            best_name_type = max(name_scores, key=name_scores.get)
            if name_scores[best_name_type] > 0.3 and confidence < 0.7:
                predicted_type = best_name_type
                confidence = max(confidence, 0.5)

        # Build alternatives
        top_indices = np.argsort(proba)[::-1][:4]
        alternatives = [
            {"type": self._type_list[i], "score": round(float(proba[i]), 3)}
            for i in top_indices
            if self._type_list[i] != predicted_type and proba[i] > 0.05
        ][:3]

        return {
            "column_name": column_name,
            "predicted_type": predicted_type,
            "confidence": round(confidence, 3),
            "method": "ml",
            "alternatives": alternatives,
        }

    def _extract_features(self, series: pd.Series, sample: pd.Series) -> list[float]:
        """Extract 16 features from a column for ML prediction."""
        if len(sample) == 0:
            return [0.0] * 16

        str_sample = sample.astype(str)
        all_chars = "".join(str_sample)
        total_chars = max(len(all_chars), 1)

        # Basic character ratios
        pct_numeric = sum(c.isdigit() for c in all_chars) / total_chars
        pct_alpha = sum(c.isalpha() for c in all_chars) / total_chars
        pct_special = 1.0 - pct_numeric - pct_alpha

        # Length stats
        lengths = str_sample.str.len()
        avg_length = float(lengths.mean())

        # Uniqueness
        unique_ratio = series.nunique() / max(len(series), 1)

        # Character presence
        has_at = float(any("@" in s for s in str_sample))
        has_dot = float(any("." in s for s in str_sample))
        has_dash = float(any("-" in s for s in str_sample))
        has_plus = float(any("+" in s for s in str_sample))
        has_colon = float(any(":" in s for s in str_sample))

        # Pattern match percentages
        def pct_match(pattern_name: str) -> float:
            if pattern_name not in _PATTERNS:
                return 0.0
            p = _PATTERNS[pattern_name]
            return float(str_sample.apply(lambda x: bool(p.match(x.strip()))).sum()) / len(str_sample)

        email_pct = pct_match("email")
        phone_pct = pct_match("phone")
        date_pct = pct_match("date")
        url_pct = pct_match("url")
        ip_pct = pct_match("ip_address")
        uuid_pct = pct_match("uuid")

        return [
            pct_numeric, pct_alpha, pct_special, avg_length,
            unique_ratio, has_at, has_dot, has_dash, has_plus, has_colon,
            email_pct, phone_pct, date_pct, url_pct, ip_pct, uuid_pct,
        ]
