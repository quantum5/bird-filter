import unittest
from pathlib import Path

from aspa.data import parse_json


class ParserTest(unittest.TestCase):
    def test_parse(self):
        with open(Path(__file__).parent / 'example.json') as f:
            result = parse_json(f.read())

        self.assertEqual(len(result), 69)

        for aspa in result:
            if aspa.customer == 54148:
                self.assertEqual(aspa.providers, [835, 924, 6939, 20473, 21738, 34927, 37988, 47272, 50917, 53667])
                self.assertEqual(aspa.ta, 'arin')
