from itertools import chain, dropwhile

from aspa.data import ASPA


class Validator:
    def __init__(self, aspas: list[ASPA]):
        self.aspas = {aspa.customer: aspa for aspa in aspas}

    def is_invalid_pair(self, upstream: int, downstream: int) -> bool:
        if downstream not in self.aspas:
            return False

        return upstream not in self.aspas[downstream].providers

    def is_aspa_invalid_customer(self, my_asn: int, bgp_path: list[int]) -> bool:
        for prev_asn, asn in zip(chain([my_asn], bgp_path), bgp_path):
            # Ignore AS-path prepends
            if prev_asn == asn:
                continue

            if self.is_invalid_pair(prev_asn, asn):
                return True

        return False

    def is_aspa_invalid_peer(self, bgp_path: list[int]) -> bool:
        for prev_asn, asn in zip(bgp_path, bgp_path[1:]):
            if prev_asn == asn:
                continue

            if self.is_invalid_pair(prev_asn, asn):
                return True

        return False

    def is_aspa_invalid_upstream(self, my_asn: int, bgp_path: list[int]) -> bool:
        max_up_ramp = len(bgp_path)
        min_down_ramp = 0

        for i, (prev_asn, asn) in enumerate(zip(chain([my_asn], bgp_path), bgp_path)):
            if prev_asn == asn:
                continue

            if self.is_invalid_pair(asn, prev_asn):
                max_up_ramp = min(max_up_ramp, i)

            if self.is_invalid_pair(prev_asn, asn):
                min_down_ramp = max(min_down_ramp, i)

        return min_down_ramp > max_up_ramp


class BirdValidator(Validator):
    """Validator coded with only language features available in bird DSL."""

    def is_aspa_invalid_customer(self, my_asn: int, bgp_path: list[int]) -> bool:
        prev_asn = my_asn

        for asn in bgp_path:
            if prev_asn != asn and self.is_invalid_pair(prev_asn, asn):
                return True
            prev_asn = asn

        return False

    def is_aspa_invalid_peer(self, bgp_path: list[int]) -> bool:
        prev_asn = bgp_path[0]

        for asn in bgp_path:
            if prev_asn != asn and self.is_invalid_pair(prev_asn, asn):
                return True
            prev_asn = asn

        return False

    def is_aspa_invalid_upstream(self, my_asn: int, bgp_path: list[int]) -> bool:
        prev_asn = my_asn
        max_up_ramp = len(bgp_path)
        min_down_ramp = 0
        i = 0

        for asn in bgp_path:
            if prev_asn != asn:
                if self.is_invalid_pair(asn, prev_asn) and max_up_ramp > i:
                    max_up_ramp = i

                if self.is_invalid_pair(prev_asn, asn):
                    min_down_ramp = i

            prev_asn = asn
            i = i + 1

        return min_down_ramp > max_up_ramp
