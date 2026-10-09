from bond import price_bond_from_path


class BondPortfolio:
    def __init__(self):
        self.bonds = []

    def add_bond(self, face, coupon_rate, maturity, weight):
        self.bonds.append({
            "face": face,
            "coupon_rate": coupon_rate,
            "maturity": maturity,
            "weight": weight,
        })

    def market_value(self, rate_path):
        total_value = 0.0

        for bond in self.bonds:
            value = price_bond_from_path(
                rate_path,
                face=bond["face"],
                coupon_rate=bond["coupon_rate"],
                maturity=bond["maturity"],
            )

            total_value += bond["weight"] * value

        return total_value
