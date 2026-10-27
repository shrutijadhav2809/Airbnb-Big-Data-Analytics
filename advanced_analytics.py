
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "airbnb_cleaned.csv"


def load_listings():
    """Load the existing cleaned Airbnb listings."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    required = {"name", "state", "roomType", "price"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price", "state", "roomType"])
    df = df[df["price"] > 0].copy()

    return df


def recommend_prices(df):
    """
    Estimate suggested listing prices using the median price
    for comparable room types within each state.

    This is a pricing benchmark, not a future-demand prediction.
    """
    df = df.copy()

    benchmarks = (
        df.groupby(["state", "roomType"])["price"]
        .agg(
            market_median="median",
            market_average="mean",
            comparable_listings="count",
        )
        .reset_index()
    )

    recommendations = df.merge(
        benchmarks,
        on=["state", "roomType"],
        how="left",
    )

    recommendations["suggested_price"] = (
        recommendations["market_median"].round(2)
    )

    recommendations["price_difference"] = (
        recommendations["suggested_price"]
        - recommendations["price"]
    ).round(2)

    recommendations["pricing_signal"] = np.select(
        [
            recommendations["price"]
            < recommendations["market_median"] * 0.90,
            recommendations["price"]
            > recommendations["market_median"] * 1.10,
        ],
        [
            "Below comparable-market range",
            "Above comparable-market range",
        ],
        default="Near comparable-market range",
    )

    return recommendations


def get_market_summary(recommendations):
    """Summarize the pricing benchmarks."""
    return (
        recommendations.groupby("state")
        .agg(
            listing_count=("name", "count"),
            average_price=("price", "mean"),
            median_price=("price", "median"),
            average_suggested_price=("suggested_price", "mean"),
        )
        .round(2)
        .sort_values("listing_count", ascending=False)
        .reset_index()
    )


if __name__ == "__main__":
    listings = load_listings()
    results = recommend_prices(listings)
    summary = get_market_summary(results)

    output_dir = BASE_DIR / "advanced_results"
    output_dir.mkdir(exist_ok=True)

    results.to_csv(
        output_dir / "dynamic_pricing_recommendations.csv",
        index=False,
    )
    summary.to_csv(
        output_dir / "market_pricing_summary.csv",
        index=False,
    )

    print("Dynamic pricing benchmark completed.")
    print(f"Listings analysed: {len(results)}")
    print(f"States analysed: {results['state'].nunique()}")
    print(f"Results saved to: {output_dir}")
    print("\nSample recommendations:")
    print(
        results[
            [
                "name",
                "state",
                "roomType",
                "price",
                "suggested_price",
                "pricing_signal",
            ]
        ].head(10).to_string(index=False)
    )
