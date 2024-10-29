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

    def is_aspa_invalid_peer(self, peer_asn: int, bgp_path: list[int]) -> bool:
        remove_peer = list(dropwhile(lambda asn: asn != peer_asn, bgp_path))

        for prev_asn, asn in zip(chain([peer_asn], remove_peer), remove_peer):
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
