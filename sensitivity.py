import numpy as np

from bond import price_bond_from_path
from alm import price_asset_portfolio_from_path, price_liability_from_path


def liability_pv01(rate_path, annual_payment=10, years=15, steps_per_year=252):
    """Estimate the liability value decrease for a one-basis-point rate increase."""
    rates = np.asarray(rate_path, dtype=float)
    if rates.ndim != 1 or not np.isfinite(rates).all():
        raise ValueError("rate_path must be a finite one-dimensional array")
    if years <= 0 or steps_per_year <= 0:
        raise ValueError("years and steps_per_year must be positive")
    if len(rates) < years * steps_per_year:
        raise ValueError("rate_path does not cover the liability payments")
    if not np.isfinite(annual_payment) or annual_payment < 0:
        raise ValueError("annual_payment must be nonnegative and finite")

    bump = 1 / 10000
    up_value = price_liability_from_path(
        rates + bump, annual_payment, years, steps_per_year,
    )
    down_value = price_liability_from_path(
        rates - bump, annual_payment, years, steps_per_year,
    )

    return float((down_value - up_value) / 2)


def bond_sensitivity(
    rate_path,
    bump_bp=1.0,
    face=100,
    coupon_rate=0.05,
    maturity=10,
    steps_per_year=252,
):
    """Measure sensitivity to a parallel shift of the short-rate path."""
    rates = np.asarray(rate_path, dtype=float)

    if rates.ndim != 1 or not np.isfinite(rates).all():
        raise ValueError("rate_path must be a finite one-dimensional array")
    if maturity <= 0 or steps_per_year <= 0:
        raise ValueError("maturity and steps_per_year must be positive")
    if len(rates) < maturity * steps_per_year:
        raise ValueError("rate_path does not cover the bond's maturity")
    if not np.isfinite(bump_bp) or bump_bp <= 0:
        raise ValueError("bump_bp must be positive and finite")

    bump = bump_bp / 10_000

    def price(path):
        return price_bond_from_path(
            path,
            face=face,
            coupon_rate=coupon_rate,
            maturity=maturity,
            steps_per_year=steps_per_year,
        )

    base_price = price(rates)
    up_price = price(rates + bump)
    down_price = price(rates - bump)

    if not np.isfinite([base_price, up_price, down_price]).all():
        raise ValueError("Prices must be finite")
    if base_price <= 0:
        raise ValueError("Base price must be positive")

    dollar_duration = (down_price - up_price) / (2 * bump)
    dollar_convexity = (up_price - 2 * base_price + down_price) / bump**2

    return {
        "price": float(base_price),
        "pv01": float(dollar_duration / 10_000),
        "duration": float(dollar_duration / base_price),
        "convexity": float(dollar_convexity / base_price),
    }


def portfolio_sensitivity(rate_path, bump_bp=1.0):
    """Measure sensitivity of the fixed 2Y/5Y/10Y asset portfolio."""
    rates = np.asarray(rate_path, dtype=float)

    if rates.ndim != 1 or len(rates) < 10 * 252:
        raise ValueError("Provide a rate path covering at least 10 years")
    if not np.isfinite(rates).all():
        raise ValueError("Rates must be finite")
    if not np.isfinite(bump_bp) or bump_bp <= 0:
        raise ValueError("bump_bp must be positive and finite")

    bump = bump_bp / 10000
    base_value = price_asset_portfolio_from_path(rates)
    up_value = price_asset_portfolio_from_path(rates + bump)
    down_value = price_asset_portfolio_from_path(rates - bump)

    if not np.isfinite([base_value, up_value, down_value]).all():
        raise ValueError("Portfolio values must be finite")
    if base_value <= 0:
        raise ValueError("Base portfolio value must be positive")

    dollar_duration = (down_value - up_value) / (2 * bump)
    dollar_convexity = (up_value - 2 * base_value + down_value) / bump**2

    return {
        "value": float(base_value),
        "pv01": float(dollar_duration / 10000),
        "duration": float(dollar_duration / base_value),
        "convexity": float(dollar_convexity / base_value),
    }


def surplus_pv01(rate_path, annual_payment=10, years=15):
    """Estimate the surplus decrease for a one-basis-point rate increase."""
    asset_pv01 = portfolio_sensitivity(rate_path)["pv01"]
    payment_pv01 = liability_pv01(rate_path, annual_payment=annual_payment, years=years)

    return asset_pv01 - payment_pv01
