import numpy as np
import pandas as pd


SIGNAL_COLUMNS = [
    "accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z",
    "heart_rate", "spo2", "sbp", "dbp",
]


def window_features(window: pd.DataFrame) -> dict[str, float]:
    features = {}
    for column in SIGNAL_COLUMNS:
        values = pd.to_numeric(
            window.get(column, pd.Series(dtype=float)), errors="coerce"
        ).dropna().to_numpy()
        features[f"{column}_mean"] = float(np.mean(values)) if len(values) else 0.0
        features[f"{column}_std"] = float(np.std(values)) if len(values) else 0.0
        features[f"{column}_min"] = float(np.min(values)) if len(values) else 0.0
        features[f"{column}_max"] = float(np.max(values)) if len(values) else 0.0

    if all(column in window for column in ["accel_x", "accel_y", "accel_z"]):
        accel = window[["accel_x", "accel_y", "accel_z"]].apply(
            pd.to_numeric, errors="coerce"
        ).to_numpy(float)
        magnitude = np.linalg.norm(accel, axis=1)
        jerk = np.diff(magnitude)
        features["accel_mag_mean"] = float(np.nanmean(magnitude))
        features["accel_mag_std"] = float(np.nanstd(magnitude))
        features["accel_mag_max"] = float(np.nanmax(magnitude))
        features["jerk_std"] = float(np.nanstd(jerk)) if len(jerk) else 0.0
        features["jerk_max"] = float(np.nanmax(np.abs(jerk))) if len(jerk) else 0.0
    return features


def make_windows(
    dataframe: pd.DataFrame, window_size: int = 40, stride: int = 20
) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_rows = []
    metadata_rows = []
    for start in range(0, max(0, len(dataframe) - window_size + 1), stride):
        window = dataframe.iloc[start:start + window_size]
        if len(window) < window_size:
            continue
        feature_rows.append(window_features(window))

        def mode(column):
            if column in window and window[column].notna().any():
                return str(window[column].mode().iloc[0])
            return "UNKNOWN"

        metadata_rows.append({
            "activity": mode("activity"),
            "fall_state": mode("fall_state"),
            "physiology_state": mode("physiology_state"),
            "subject_id": str(window["subject_id"].iloc[0])
            if "subject_id" in window else "unknown",
            "source_dataset": str(window["source_dataset"].iloc[0])
            if "source_dataset" in window else "unknown",
        })
    return pd.DataFrame(feature_rows), pd.DataFrame(metadata_rows)
