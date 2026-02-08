import numpy as np
import pandas as pd
import argparse

"""
Generates large, realistic fake telemetry for Lap Time Bottleneck Finder

Output:
  data/big_telemetry.csv

Features:
- 30 laps
- 3000 samples per lap
- Multiple corners
- Random weak braking corners
- Random weak exit corners
- Creates braking loss, exit loss, and late throttle loss patterns
"""


def main():
    parser = argparse.ArgumentParser(description="Generate fake telemetry for Lap Time Bottleneck Finder")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (optional)")
    parser.add_argument("--laps", type=int, default=30, help="Number of laps")
    parser.add_argument("--points", type=int, default=3000, help="Points per lap")
    parser.add_argument("--out", type=str, default="data/big_telemetry.csv", help="Output CSV path")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    ROWS = []
    timestamp = 0.0

    LAPS = args.laps
    POINTS_PER_LAP = args.points

    # Corner zones (normalized track position)
    CORNERS = [
        (0.10, 0.18),
        (0.32, 0.40),
        (0.55, 0.65),   # big hairpin
        (0.78, 0.86)
    ]

    for lap in range(1, LAPS + 1):
        # Pick lap's primary weakness type
        weakness = rng.choice(["braking", "exit", "late_throttle"], p=[0.35, 0.35, 0.30])
        weak_exit_corner = rng.choice(len(CORNERS))
        weak_brake_corner = rng.choice(len(CORNERS))

        for i in range(POINTS_PER_LAP):
            pos = i / POINTS_PER_LAP
            # Base timestep ~22 Hz
            dt = 0.045 + rng.normal(0, 0.002)
            speed = rng.normal(155, 4)
            throttle = np.clip(rng.normal(0.75, 0.1), 0, 1)
            brake = np.clip(rng.normal(0.05, 0.05), 0, 1)
            steering = rng.normal(0, 0.15)

            for idx, (c_start, c_end) in enumerate(CORNERS):
                if c_start <= pos <= c_end:
                    # Simulate corner behavior
                    speed -= 40
                    throttle *= 0.55
                    brake += 0.4
                    steering += rng.normal(0.4, 0.1)

                    corner_len = (c_end - c_start)
                    midpoint = (c_start + c_end) / 2
                    entry_end = c_start + 0.25 * corner_len    # first 25% = braking/entry
                    exit_start = c_end - 0.25 * corner_len     # last 25% = exit/traction

                    # Exit phase base behaviour (normal laps): start re-applying throttle after apex.
                    # We want most laps to go ABOVE the analyzer throttle threshold (default 0.25)
                    # shortly after the midpoint, otherwise the analyzer will always flag "late throttle".
                    if pos > midpoint:
                        # Normal exit: throttle comes back up.
                        throttle = max(throttle, 0.60)

                        # Release brake on exit for most laps, but for braking-weak laps
                        # we keep a little extra brake longer (this makes brake_time_loss win sometimes).
                        if weakness == "braking" and idx == weak_brake_corner:
                            brake = min(brake, 0.22)
                        else:
                            brake = min(brake, 0.10)

                    # --- Weakness injections ---
                    # 1) Braking-dominant lap: bigger dt hit, but only early in the corner
                    entry_end_strong = c_start + 0.40 * corner_len  # first 40% of corner
                    if weakness == "braking" and idx == weak_brake_corner and c_start <= pos <= entry_end_strong:
                        dt += 0.060

                    # 2) Exit-dominant lap: dt hit only in the last quarter of the corner
                    exit_start_tight = c_end - 0.15 * corner_len  # last 15% only
                    if weakness == "exit" and idx == weak_exit_corner and exit_start_tight <= pos <= c_end:
                        dt += 0.020

                    # 3) Late throttle lap: keep throttle low after apex until later, and add a small dt hit
                    if weakness == "late_throttle" and idx == weak_exit_corner and pos > midpoint:
                        # Keep throttle BELOW the analyzer threshold for most of the exit,
                        # but keep the dt penalty modest so this shows up primarily as
                        # exit_throttle_delay_loss (not always as the biggest exit_time_loss).
                        delay_release = c_end - 0.12 * corner_len  # release throttle in last ~12% of corner
                        if pos < delay_release:
                            throttle = min(throttle, 0.12)  # < 0.25
                            brake = min(brake, 0.08)
                            dt += 0.012
                        else:
                            throttle = max(throttle, 0.70)
                            brake = min(brake, 0.05)

            timestamp += dt
            ROWS.append([
                timestamp,
                lap,
                speed,
                throttle,
                brake,
                steering,
                pos
            ])

    df = pd.DataFrame(
        ROWS,
        columns=[
            "timestamp",
            "lap",
            "speed",
            "throttle",
            "brake",
            "steering",
            "track_position"
        ]
    )

    df.to_csv(args.out, index=False)
    print(f"✅ Created {args.out}")
    print(f"Rows: {len(df)}")
    print(f"Laps: {LAPS}")
    print(f"Samples per lap: {POINTS_PER_LAP}")


if __name__ == "__main__":
    main()