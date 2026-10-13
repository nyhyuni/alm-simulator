# ALM Simulator

An interactive Python app for exploring how interest rates affect an insurer’s assets, future payments and surplus.

## What it shows

- Interest-rate scenarios generated with Vasicek or a random walk with drift.
- The present value of a bond portfolio and fixed annual liability payments.
- Surplus across scenarios: asset value minus liability value.
- Estimated changes in assets, liabilities, and surplus when rates rise by 1 basis point.

## Run locally

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python server.py --port 8001
```

Open [localhost:8001](http://localhost:8001/) and change the assumptions to compare results. The frontend uses plain HTML, CSS, and JavaScript with a Python server.

To run the calculations without the frontend:

```sh
.venv/bin/python simulation.py
```

## Model assumptions

The asset portfolio is a weighted mix of three bonds:

| Maturity | Annual coupon | Weight |
| --- | --- | --- |
| 2 years | 3.5% | 25% |
| 5 years | 4.5% | 35% |
| 10 years | 5.0% | 40% |

Each bond has face value 100, and portfolio weights stay fixed.

Liabilities default to payments of 10 at the end of each year for 15 years. All cash flows use continuous discounting along simulated rate paths, with 252 steps per year.

Sensitivities shift the entire rate path by ±1 basis point with fixed cash flows. The interface shows the estimated change for a +1 bp move as −PV01.

Values are illustrative model units. This simplified model excludes market calibration, credit risk, reinvestment, rebalancing, and insurance features such as mortality and lapses. It is not a regulatory solvency model. The chart’s 90% rate range applies at each point in time.

## Development

Developed with AI assistance for code, the frontend, debugging, and documentation.
