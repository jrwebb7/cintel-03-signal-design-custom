"""Compare request-weighted reliability across request-volume groups."""

from pathlib import Path

import polars as pl

from cintel.utils_system import load_system_metrics


def compare_volume(metrics: pl.DataFrame) -> pl.DataFrame:
    """Summarize observations at or below the median and above the median."""
    active = metrics.filter(pl.col("requests") > 0)
    median = active["requests"].median()
    if median is None:
        raise ValueError(
            "Volume comparison requires at least one positive request count."
        )

    return (
        active.with_columns(
            pl.when(pl.col("requests") <= median)
            .then(pl.lit("lower"))
            .otherwise(pl.lit("higher"))
            .alias("volume_group")
        )
        .group_by("volume_group")
        .agg(
            pl.len().alias("observations"),
            pl.col("requests").sum(),
            pl.col("errors").sum(),
            pl.col("total_latency_ms").sum(),
        )
        .with_columns(
            (pl.col("errors") / pl.col("requests")).alias("error_rate"),
            (1 - pl.col("errors") / pl.col("requests")).alias("success_rate"),
            (pl.col("total_latency_ms") / pl.col("requests")).alias("avg_latency_ms"),
        )
        .sort("volume_group", descending=True)
    )


def main() -> None:
    """Write and display the request-volume comparison."""
    metrics = load_system_metrics(Path("data/system_metrics.csv"))
    output = Path("artifacts/volume_comparison.csv")
    output.parent.mkdir(exist_ok=True)
    summary = compare_volume(metrics)
    summary.write_csv(output)
    print(summary)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
