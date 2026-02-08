import pandas as pd
import numpy as np

"""Telemetry analysis utilities.

What this module does (upgraded):
- Load CSV telemetry
- Segment the lap by normalized track_position (0..1)
- Compute per-sample dt within each lap
- Compute per-lap/per-segment timing
- Rank bottlenecks by time loss vs the best lap

New (useful output):
- brake_time_loss: extra time spent *with brake applied* vs best lap
- exit_time_loss: extra time spent after the segment's min-speed point (apex proxy)
- exit_throttle_delay_loss: extra time after min-speed until throttle re-application
- top_cause: simple label explaining likely cause (braking vs corner_exit vs late throttle)

These are heuristics (no track map needed), but they produce actionable output.
"""


REQUIRED_COLUMNS = [
    "timestamp",
    "lap",
    "speed",
    "throttle",
    "brake",
    "steering",
    "track_position",
]


def load_data(path_or_buffer) -> pd.DataFrame:
    """Load telemetry data from a CSV file or file-like object."""
    return pd.read_csv(path_or_buffer)


def validate_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Validate columns, coerce types, clip common ranges, and sort."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Coerce numeric columns
    for c in REQUIRED_COLUMNS:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["timestamp", "lap", "track_position"])  # essential columns

    # Clip common ranges
    df["track_position"] = df["track_position"].clip(0.0, 1.0)
    df["throttle"] = df["throttle"].clip(0.0, 1.0)
    df["brake"] = df["brake"].clip(0.0, 1.0)

    # Sort for correct dt computation
    df = df.sort_values(["lap", "timestamp"]).reset_index(drop=True)
    return df


def assign_segment(pos: float, n_segments: int = 4) -> str:
    """Determine which segment a given track position belongs to."""
    if pos is None or pd.isna(pos) or pos < 0:
        return "S1"

    seg_length = 1.0 / n_segments
    seg_idx = int(pos / seg_length)
    if seg_idx >= n_segments:
        seg_idx = n_segments - 1
    return f"S{seg_idx + 1}"


def add_segments(df: pd.DataFrame, n_segments: int = 4) -> pd.DataFrame:
    """Add a `segment` column based on track_position."""
    df = df.copy()
    df["segment"] = df["track_position"].apply(lambda p: assign_segment(p, n_segments))
    return df


def compute_deltas(df: pd.DataFrame) -> pd.DataFrame:
    """Compute dt within each lap."""
    df = df.copy()
    df = df.sort_values(["lap", "timestamp"]).reset_index(drop=True)
    df["dt"] = df.groupby("lap")["timestamp"].diff()
    return df


def clean_deltas(df: pd.DataFrame, max_dt: float | None = None) -> pd.DataFrame:
    """Keep only valid dt values (positive and optionally under max_dt)."""
    df = df.copy()
    df = df.dropna(subset=["dt"])
    df = df[df["dt"] > 0]
    if max_dt is not None:
        df = df[df["dt"] <= max_dt]
    return df


def _per_lap_segment_metrics(
    df: pd.DataFrame,
    brake_threshold: float = 0.15,
    throttle_threshold: float = 0.25,
) -> pd.DataFrame:
    """Compute per-lap/per-segment timing + driver-input heuristics."""

    df = df.copy()
    df["is_braking"] = df["brake"] >= brake_threshold
    df["is_throttle"] = df["throttle"] >= throttle_threshold
    df["is_coast"] = ~(df["is_braking"] | df["is_throttle"])

    rows: list[dict] = []

    for (lap, seg), g in df.groupby(["lap", "segment"], sort=False):
        g = g.sort_values("timestamp")

        seg_dt = float(g["dt"].sum())
        brake_dt = float(g.loc[g["is_braking"], "dt"].sum())
        throttle_dt = float(g.loc[g["is_throttle"], "dt"].sum())
        coast_dt = float(g.loc[g["is_coast"], "dt"].sum())

        # Apex proxy: minimum speed within the segment.
        # Entry = start -> min speed.
        # Exit (powered) = throttle re-application -> end of segment.
        # Throttle delay = min speed -> throttle re-application.
        if len(g) >= 2 and g["speed"].notna().any():
            g2 = g.reset_index(drop=True)

            apex_pos = int(g2["speed"].idxmin())
            entry_dt = float(g2.loc[:apex_pos, "dt"].sum())

            after_apex = g2.loc[apex_pos + 1 :]
            if after_apex.empty:
                exit_throttle_delay_dt = 0.0
                exit_dt = 0.0
            else:
                throttle_on_pos = after_apex.index[after_apex["is_throttle"]]
                if len(throttle_on_pos) == 0:
                    # Never got back on throttle in this segment after the apex.
                    # Treat all remaining time as "delay" and 0 powered exit.
                    exit_throttle_delay_dt = float(after_apex["dt"].sum())
                    exit_dt = 0.0
                else:
                    first_on = int(throttle_on_pos[0])
                    # Delay includes time from just after apex up to and including first throttle-on sample.
                    exit_throttle_delay_dt = float(g2.loc[apex_pos + 1 : first_on, "dt"].sum())
                    # Powered exit time starts at throttle re-application.
                    exit_dt = float(g2.loc[first_on:, "dt"].sum())
        else:
            entry_dt = np.nan
            exit_dt = np.nan
            exit_throttle_delay_dt = np.nan

        rows.append(
            {
                "lap": int(lap),
                "segment": str(seg),
                "seg_dt": seg_dt,
                "brake_dt": brake_dt,
                "throttle_dt": throttle_dt,
                "coast_dt": coast_dt,
                "entry_dt": entry_dt,
                "exit_dt": exit_dt,
                "exit_throttle_delay_dt": exit_throttle_delay_dt,
                "avg_speed": float(g["speed"].mean()),
                "avg_throttle": float(g["throttle"].mean()),
                "avg_brake": float(g["brake"].mean()),
            }
        )

    return pd.DataFrame(rows)


def analyse_telemetry(
    df: pd.DataFrame,
    n_segments: int = 4,
    max_dt: float | None = None,
    brake_threshold: float = 0.15,
    throttle_threshold: float = 0.25,
) -> pd.DataFrame:
    """Full analysis pipeline returning ranked bottlenecks with useful breakdowns."""

    df = validate_and_clean(df)
    df = add_segments(df, n_segments=n_segments)
    df = compute_deltas(df)
    df = clean_deltas(df, max_dt=max_dt)

    per_lap = _per_lap_segment_metrics(
        df,
        brake_threshold=brake_threshold,
        throttle_threshold=throttle_threshold,
    )

    if per_lap.empty:
        return pd.DataFrame(
            columns=[
                "segment",
                "avg_dt",
                "best_dt",
                "time_loss",
                "loss_percent",
                "brake_time_loss",
                "exit_time_loss",
                "exit_throttle_delay_loss",
                "top_cause",
                "avg_speed",
                "avg_throttle",
                "avg_brake",
            ]
        )

    g = per_lap.groupby("segment", as_index=False)

    avg = g.agg(
        avg_dt=("seg_dt", "mean"),
        avg_brake_dt=("brake_dt", "mean"),
        avg_exit_dt=("exit_dt", "mean"),
        avg_exit_throttle_delay_dt=("exit_throttle_delay_dt", "mean"),
        avg_speed=("avg_speed", "mean"),
        avg_throttle=("avg_throttle", "mean"),
        avg_brake=("avg_brake", "mean"),
        avg_entry_dt=("entry_dt", "mean"),
    )

    # Baseline: choose ONE best lap per segment by overall segment time.
    # This keeps component losses comparable to total time_loss.
    baseline_idx = per_lap.groupby("segment")["seg_dt"].idxmin()
    baseline = per_lap.loc[baseline_idx, [
        "segment",
        "seg_dt",
        "brake_dt",
        "exit_dt",
        "exit_throttle_delay_dt",
        "entry_dt",
    ]].rename(
        columns={
            "seg_dt": "best_dt",
            "brake_dt": "best_brake_dt",
            "exit_dt": "best_exit_dt",
            "exit_throttle_delay_dt": "best_exit_throttle_delay_dt",
            "entry_dt": "best_entry_dt",
        }
    )

    out = avg.merge(baseline, on="segment", how="left")

    # Overall time loss
    out["time_loss"] = out["avg_dt"] - out["best_dt"]
    out["loss_percent"] = np.where(
        out["best_dt"] > 0,
        (out["time_loss"] / out["best_dt"]) * 100.0,
        np.nan,
    )

    # Actionable breakdown
    out["brake_time_loss"] = out["avg_brake_dt"] - out["best_brake_dt"]
    out["exit_time_loss"] = out["avg_exit_dt"] - out["best_exit_dt"]
    out["exit_throttle_delay_loss"] = (
        out["avg_exit_throttle_delay_dt"] - out["best_exit_throttle_delay_dt"]
    )
    out["entry_time_loss"] = out["avg_entry_dt"] - out["best_entry_dt"]

    # Clamp tiny negatives from noise to 0 for cleaner UI
    for c in [
        "time_loss",
        "brake_time_loss",
        "exit_time_loss",
        "exit_throttle_delay_loss",
        "entry_time_loss",
    ]:
        out[c] = out[c].where(out[c] > 1e-9, 0.0)

    # Explain the biggest positive contributor
    def _top_cause(row) -> str:
        candidates = {
            "braking": row.get("brake_time_loss", 0.0),
            "corner_exit": row.get("exit_time_loss", 0.0),
            "corner_exit (late throttle)": row.get("exit_throttle_delay_loss", 0.0),
        }
        best_label = max(
            candidates,
            key=lambda k: candidates[k] if pd.notna(candidates[k]) else -np.inf,
        )
        if pd.isna(candidates[best_label]) or candidates[best_label] <= 1e-6:
            return "n/a"
        return best_label

    out["top_cause"] = out.apply(_top_cause, axis=1)

    # Keep a backwards-compatible alias for older frontend code
    out["loss"] = out["time_loss"]

    # Rank
    out = out.sort_values("time_loss", ascending=False).reset_index(drop=True)
    return out