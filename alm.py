import numpy as np
import matplotlib.pyplot as plt

from vasicek import simulate_vasicek_paths
from bond import price_bond_from_path


def price_liability_from_path(
    rate_path,
    annual_payment=10,
    years=15,
    steps_per_year=252,
):
    pv = 0.0

    for year in range(1, years + 1):
        step = year * steps_per_year
        accumulated_rate = np.sum(rate_path[:step]) / steps_per_year
        discount_factor = np.exp(-accumulated_rate)

        pv += annual_payment * discount_factor

    return pv


def price_asset_portfolio_from_path(rate_path):
    portfolio = [
        {"name": "2Y Bond", "face": 100, "coupon_rate": 0.035, "maturity": 2, "weight": 0.25},
        {"name": "5Y Bond", "face": 100, "coupon_rate": 0.045, "maturity": 5, "weight": 0.35},
        {"name": "10Y Bond", "face": 100, "coupon_rate": 0.050, "maturity": 10, "weight": 0.40},
    ]

    total_value = 0.0

    for bond in portfolio:
        value = price_bond_from_path(
            rate_path,
            face=bond["face"],
            coupon_rate=bond["coupon_rate"],
            maturity=bond["maturity"],
        )

        total_value += bond["weight"] * value

    return total_value


def run_alm_simulation(paths):
    asset_values = []
    liability_values = []
    surplus_values = []

    for col in paths.columns:
        rate_path = paths[col].values

        asset_value = price_asset_portfolio_from_path(rate_path)
        liability_value = price_liability_from_path(rate_path)
        surplus = asset_value - liability_value

        asset_values.append(asset_value)
        liability_values.append(liability_value)
        surplus_values.append(surplus)

    return (
        np.array(asset_values),
        np.array(liability_values),
        np.array(surplus_values),
    )


def print_summary(name, values):
    print(f"\n{name}")
    print("Mean:", values.mean())
    print("Median:", np.median(values))
    print("5th percentile:", np.percentile(values, 5))
    print("95th percentile:", np.percentile(values, 95))
    print("Min:", values.min())
    print("Max:", values.max())


def plot_distribution(values, title, xlabel):
    plt.figure(figsize=(10, 6))
    plt.hist(values, bins=40)
    plt.xlabel(xlabel)
    plt.ylabel("Frequency")
    plt.title(title)
    plt.show()


if __name__ == "__main__":
    paths = simulate_vasicek_paths(years=15)

    asset_values, liability_values, surplus_values = run_alm_simulation(paths)

    print_summary("Asset Value Distribution", asset_values)
    print_summary("Liability Value Distribution", liability_values)
    print_summary("Surplus Distribution", surplus_values)

    plot_distribution(asset_values, "Asset Value Distribution", "Asset Value")
    plot_distribution(liability_values, "Liability Value Distribution", "Liability Value")
    plot_distribution(surplus_values, "ALM Surplus Distribution", "Surplus = Assets - Liabilities")
