# ALM Simulator

Python project for studying how interest rates affect bond values and a simple asset-liability portfolio.

## What it does

* Simulates interest rates using Vasicek and Brownian motion with drift
* Discounts bond and liability cash flows along rate paths
* Calculates asset values, liability values, and surplus across scenarios
* Estimates bond and portfolio PV01, duration, and convexity

## Run

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python alm.py
```

The example runs 15-year scenarios and plots asset, liability, and surplus distributions. Close each plot to see the next one.

## Assumptions

The example uses 2-, 5-, and 10-year bonds and fixed annual liability payments over 15 years. Surplus is asset value minus liability value. Sensitivity calculations shift the entire rate path up and down while keeping cash flows fixed.

This is a simplified model with illustrative values, without market calibration, credit risk, rebalancing, or insurance features such as mortality and lapses.
