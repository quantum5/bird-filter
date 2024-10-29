import json
import re
from dataclasses import dataclass
from typing import Optional

reasn = re.compile(r"^AS(\d+)$")


def parse_asn(text: str) -> Optional[int]:
    match = reasn.match(text)
    if match:
        return int(match.group(1))


@dataclass
class ASPA:
    customer: int
    providers: list[int]
    ta: str

    @classmethod
    def from_dict(cls, d):
        try:
            customer = parse_asn(d['customer'])
            providers = list(map(parse_asn, d['providers']))
            return cls(customer, providers, d['ta'])
        except (KeyError, TypeError):
            return None


def parse_json(data: str) -> list[ASPA]:
    data = json.loads(data)
    return list(filter(None, map(ASPA.from_dict, data.get('aspas', []))))
