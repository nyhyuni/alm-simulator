import numpy as np

from alm import run_alm_simulation
from random_walk import simulate_random_walk_paths
from sensitivity import liability_pv01, portfolio_sensitivity
from vasicek import simulate_vasicek_paths


def run_simulation(
    model="vasicek",
    r0=0.04,
    a=0.30,
    b=0.045,
    sigma=0.01,
    annual_payment=10,
    years=15,
    n_paths=1000,
    seed=42,
):
    """Run rate scenarios and calculate ALM values and sensitivities."""
    if not isinstance(years, int) or years < 10:
        raise ValueError("years must be an integer of at least 10 to cover the bonds")
    if not isinstance(n_paths, int) or n_paths < 1:
        raise ValueError("n_paths must be a positive integer")
    if not np.isfinite(annual_payment) or annual_payment < 0:
        raise ValueError("annual_payment must be nonnegative and finite")

    if model == "vasicek":
        paths = simulate_vasicek_paths(
            r0=r0, a=a, b=b, sigma=sigma, years=years, n_paths=n_paths, seed=seed,
        )
    elif model == "random":
        paths = simulate_random_walk_paths(
            r0=r0, sigma=sigma, years=years, n_paths=n_paths, seed=seed,
        )
    else:
        raise ValueError("model must be 'vasicek' or 'random'")

    assets, liabilities, surplus = run_alm_simulation(
        paths, annual_payment=annual_payment, years=years,
    )

    asset_pv01s = []
    liability_pv01s = []
    for col in paths.columns:
        rate_path = paths[col].values
        asset = portfolio_sensitivity(rate_path)
        liability = liability_pv01(rate_path, annual_payment, years)

        asset_pv01s.append(asset["pv01"])
        liability_pv01s.append(liability)

    asset_pv01 = float(np.mean(asset_pv01s))
    payment_pv01 = float(np.mean(liability_pv01s))

    return {
        "assets": float(assets.mean()),
        "liabilities": float(liabilities.mean()),
        "surplus": float(surplus.mean()),
        "asset_pv01": asset_pv01,
        "liability_pv01": payment_pv01,
        "surplus_pv01": asset_pv01 - payment_pv01,
        "asset_values": assets.tolist(),
        "liability_values": liabilities.tolist(),
        "surplus_values": surplus.tolist(),
    }


if __name__ == "__main__":
    result = run_simulation(n_paths=100)

    for name in ("assets", "liabilities", "surplus",
                 "asset_pv01", "liability_pv01", "surplus_pv01"):
        print(f"{name}: {result[name]:.6f}")
