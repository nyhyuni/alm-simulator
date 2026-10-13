"""Run the local frontend with: .venv/bin/python server.py"""
import os
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/alm-matplotlib")

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
from simulation import run_simulation

ROOT = Path(__file__).parent / "frontend"


def simulate(p):
    if not isinstance(p, dict):
        raise ValueError("Assumptions must be a JSON object")

    years = int(p.get("years", 15))
    count = int(p.get("paths", 100))
    seed = int(p.get("seed", 42))
    r0 = float(p.get("r0", 4)) / 100
    b = float(p.get("b", 4.5)) / 100
    a = float(p.get("a", .3))
    sigma = float(p.get("sigma", 1)) / 100
    payment = float(p.get("payment", 10))

    if not 10 <= years <= 30 or not 10 <= count <= 1000:
        raise ValueError("Use 10–30 years and 10–1,000 scenarios")
    if not 0 <= seed <= 4294967295:
        raise ValueError("Use a seed between 0 and 4,294,967,295")
    if not all(np.isfinite(v) for v in (r0, b, a, sigma, payment)):
        raise ValueError("Assumptions must be finite numbers")
    if not (-.1 <= r0 <= .3 and -.1 <= b <= .3 and 0 <= a <= 5
            and 0 <= sigma <= .1 and 0 <= payment <= 1000):
        raise ValueError("Assumptions are outside the allowed ranges")

    result = run_simulation(
        model=p.get("model", "vasicek"), r0=r0, a=a, b=b, sigma=sigma,
        annual_payment=payment, years=years, n_paths=count, seed=seed,
    )
    result["assumptions"] = p
    return result


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_POST(self):
        if self.path != "/api/simulate":
            self.send_error(404)
            return
        try:
            size = int(self.headers.get("Content-Length", 0))
            if not 0 < size <= 10000:
                raise ValueError("Invalid request size")
            result = simulate(json.loads(self.rfile.read(size)))
            data = json.dumps(result, allow_nan=False).encode()
            status = 200
        except (ValueError, TypeError, KeyError, OverflowError) as error:
            data = json.dumps({"error": str(error)}).encode()
            status = 400
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    port = parser.parse_args().port
    print(f"ALM simulator → http://localhost:{port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
