import numpy as np
import matplotlib.pyplot as plt

from vasicek import simulate_vasicek_paths


def price_bond_from_path(
    rate_path,
    face=100,
    coupon_rate=0.05,
    maturity=10,
    steps_per_year=252,
):
    """
    Price a fixed-rate bond using a simulated short-rate path.
    Assumes annual coupon payments and continuous discounting from the short-rate path.
    """
    coupon = face * coupon_rate
    pv = 0.0

    for year in range(1, maturity + 1):
        step = year * steps_per_year

        # Approximate integral of short rates from time 0 to this cashflow date
        accumulated_rate = np.sum(rate_path[:step]) / steps_per_year
        discount_factor = np.exp(-accumulated_rate)

        cashflow = coupon
        if year == maturity:
            cashflow += face

        pv += cashflow * discount_factor

    return pv


def price_bond_scenarios(
    paths,
    face=100,
    coupon_rate=0.05,
    maturity=10,
    steps_per_year=252,
):
    bond_values = []

    for col in paths.columns:
        price = price_bond_from_path(
            paths[col].values,
            face=face,
            coupon_rate=coupon_rate,
            maturity=maturity,
            steps_per_year=steps_per_year,
        )
        bond_values.append(price)

    return np.array(bond_values)


def plot_bond_value_distribution(bond_values):
    plt.figure(figsize=(10, 6))
    plt.hist(bond_values, bins=40)
    plt.xlabel("Bond Value")
    plt.ylabel("Frequency")
    plt.title("10-Year Bond Value Distribution")
    plt.show()


if __name__ == "__main__":
    paths = simulate_vasicek_paths()

    bond_values = price_bond_scenarios(
        paths,
        face=100,
        coupon_rate=0.05,
        maturity=10,
    )

    print("Mean:", bond_values.mean())
    print("Median:", np.median(bond_values))
    print("5th percentile:", np.percentile(bond_values, 5))
    print("95th percentile:", np.percentile(bond_values, 95))
    print("Min:", bond_values.min())
    print("Max:", bond_values.max())

    plot_bond_value_distribution(bond_values)

def price_plain_bond_flat_rate(face=100, coupon_rate=0.05, maturity=10, y=0.04):
    pv = 0.0

    for year in range(1, maturity + 1):
        cashflow = face * coupon_rate

        if year == maturity:
            cashflow += face

        pv += cashflow / ((1 + y) ** year)

    return pv


if __name__ == "__main__":
    base_price = price_plain_bond_flat_rate(y=0.04)
    up_price = price_plain_bond_flat_rate(y=0.0401)
    down_price = price_plain_bond_flat_rate(y=0.0399)

    pv01 = (down_price - up_price) / 2

    print("Base price:", base_price)
    print("PV01:", pv01)
