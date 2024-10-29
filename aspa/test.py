import unittest
from pathlib import Path

from aspa.data import ASPA, parse_json
from aspa.validate import Validator


class ParserTest(unittest.TestCase):
    def test_parse(self):
        with open(Path(__file__).parent / 'example.json') as f:
            result = parse_json(f.read())

        self.assertEqual(len(result), 69)

        for aspa in result:
            if aspa.customer == 54148:
                self.assertEqual(aspa.providers, [835, 924, 6939, 20473, 21738, 34927, 37988, 47272, 50917, 53667])
                self.assertEqual(aspa.ta, 'arin')


class CustomerTest(unittest.TestCase):
    validator_class = Validator

    def setUp(self):
        self.validator = self.validator_class([
            ASPA(64500, [64501], 'test'),
            ASPA(64501, [64502], 'test'),
            ASPA(64502, [64503], 'test'),
            ASPA(64503, [64504], 'test'),
        ])

    def test_all_valid(self):
        self.assertFalse(self.validator.is_aspa_invalid_customer(64501, [64500]))
        self.assertFalse(self.validator.is_aspa_invalid_customer(64502, [64501, 64500]))
        self.assertFalse(self.validator.is_aspa_invalid_customer(64503, [64502, 64501, 64500]))
        self.assertFalse(self.validator.is_aspa_invalid_customer(64504, [64503, 64502, 64501, 64500]))
        self.assertFalse(self.validator.is_aspa_invalid_customer(64504, [64503, 64502, 64501]))
        self.assertFalse(self.validator.is_aspa_invalid_customer(64504, [64503, 64502]))
        self.assertFalse(self.validator.is_aspa_invalid_customer(64504, [64503]))

    def test_some_unknown(self):
        self.assertFalse(self.validator.is_aspa_invalid_customer(64505, [64504, 64503, 64502, 64501]))
        self.assertFalse(self.validator.is_aspa_invalid_customer(64503, [64502, 64501, 64505]))

    def test_all_unknown(self):
        self.assertFalse(self.validator.is_aspa_invalid_customer(64506, [64507, 64508]))

    def test_some_invalid(self):
        self.assertTrue(self.validator.is_aspa_invalid_customer(64505, [64504, 64503, 64501, 64501]))
        self.assertTrue(self.validator.is_aspa_invalid_customer(64504, [64503, 64502, 64506, 64500]))


class PeerTest(unittest.TestCase):
    validator_class = Validator

    def setUp(self):
        self.validator = self.validator_class([
            ASPA(64500, [64501], 'test'),
            ASPA(64501, [64502], 'test'),
            ASPA(64502, [64503], 'test'),
            ASPA(64503, [64504], 'test'),
        ])

    def test_all_valid(self):
        self.assertFalse(self.validator.is_aspa_invalid_peer(64501, [64501, 64500]))
        self.assertFalse(self.validator.is_aspa_invalid_peer(64502, [64502, 64501, 64500]))
        self.assertFalse(self.validator.is_aspa_invalid_peer(64503, [64503, 64502, 64501, 64500]))
        self.assertFalse(self.validator.is_aspa_invalid_peer(64504, [64504, 64503, 64502, 64501]))
        self.assertFalse(self.validator.is_aspa_invalid_peer(64504, [64504, 64503, 64502]))
        self.assertFalse(self.validator.is_aspa_invalid_peer(64504, [64504, 64503]))
        self.assertFalse(self.validator.is_aspa_invalid_peer(64504, [64504]))

    def test_prepend_valid(self):
        self.assertFalse(self.validator.is_aspa_invalid_peer(64501, [64501, 64500, 64500]))
        self.assertFalse(self.validator.is_aspa_invalid_peer(64502, [64502, 64502, 64501, 64501, 64500]))
        self.assertFalse(self.validator.is_aspa_invalid_peer(64503, [64503, 64502, 64502, 64501, 64500, 64500]))

    def test_some_unknown(self):
        self.assertFalse(self.validator.is_aspa_invalid_peer(64505, [64505, 64504, 64503, 64502]))
        self.assertFalse(self.validator.is_aspa_invalid_peer(64503, [64503, 64503, 64502, 64505]))

    def test_all_unknown(self):
        self.assertFalse(self.validator.is_aspa_invalid_customer(64506, [64506, 64507, 64508]))

    def test_some_invalid(self):
        self.assertTrue(self.validator.is_aspa_invalid_peer(64505, [64505, 64505, 64503, 64503]))
        self.assertTrue(self.validator.is_aspa_invalid_peer(64504, [64504, 64503, 64506, 64500]))

    def test_peer_originated(self):
        for i in [64500, 64501, 64502, 64503, 64504, 64505]:
            self.assertFalse(self.validator.is_aspa_invalid_peer(i, [i]))


class UpstreamTest(unittest.TestCase):
    validator_class = Validator

    def setUp(self):
        # 6451x are tier 1 ISPs
        # 6452x are tier 2 ISPs
        # 6453x are tier 3 ISPs
        self.validator = self.validator_class([
            ASPA(64510, [], 'test'),
            ASPA(64511, [], 'test'),
            ASPA(64512, [], 'test'),
            ASPA(64514, [], 'test'),
            ASPA(64520, [64510, 64511], 'test'),
            ASPA(64521, [64512, 64513], 'test'),
            ASPA(64522, [64511, 64512], 'test'),
            ASPA(64530, [64520], 'test'),
            ASPA(64531, [64521, 64523], 'test'),
        ])

    def test_all_valid(self):
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64530, [64520, 64510, 64512, 64521, 64531]))
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64520, [64510, 64512, 64521, 64531]))
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64521, [64512, 64510, 64520, 64520, 64530]))
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64531, [64521, 64512, 64510, 64520, 64530]))

    def test_valid_edge(self):
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64530, [64520, 64510]))
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64530, [64520]))
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64520, [64510]))

    def test_tier_1_tier_2_peer(self):
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64530, [64520, 64512, 64521, 64531]))
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64521, [64510, 64510, 64520, 64520, 64530]))
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64531, [64521, 64510, 64520, 64530]))
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64531, [64521, 64510, 64510, 64520, 64520]))

    def test_some_unknown(self):
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64530, [64520, 64510, 64513, 64521, 64531]))
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64520, [64510, 64513, 64521, 64531]))
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64521, [64510, 64510, 64520, 64520, 64530]))
        self.assertFalse(self.validator.is_aspa_invalid_upstream(64531, [64521, 64510, 64520, 64530]))

    def test_invalid_downramp(self):
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64530, [64520, 64510, 64512, 64522, 64531]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64530, [64520, 64510, 64512, 64531]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64531, [64521, 64512, 64510, 64530]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64531, [64521, 64512, 64510, 64522, 64530]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64530, [64520, 64512, 64522, 64531]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64521, [64510, 64510, 64520, 64522, 64530]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64521, [64510, 64510, 64522, 64520, 64530]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64530, [64520, 64510, 64522, 64531]))

    def test_invalid_upramp(self):
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64530, [64520, 64513, 64512, 64521, 64531]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64530, [64521, 64510, 64512, 64521, 64531]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64531, [64520, 64512, 64510, 64520, 64530]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64531, [64521, 64511, 64510, 64520, 64530]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64530, [64520, 64514, 64521, 64521, 64531]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64530, [64521, 64510, 64521, 64531, 64531]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64531, [64520, 64512, 64520, 64520, 64530]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64531, [64521, 64514, 64520, 64530, 64530]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64530, [64520, 64520, 64514, 64521, 64531]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64530, [64521, 64510, 64510, 64521, 64531]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64531, [64520, 64512, 64512, 64520, 64530]))
        self.assertTrue(self.validator.is_aspa_invalid_upstream(64531, [64521, 64521, 64514, 64520, 64530]))


if __name__ == '__main__':
    unittest.main()
