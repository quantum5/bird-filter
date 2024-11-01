import json
import re
from dataclasses import dataclass
from typing import Optional, Union

reasn = re.compile(r"^AS(\d+)$")


def parse_asn(value: Union[str, int]) -> Optional[int]:
    if isinstance(value, int):
        return value

    match = reasn.match(value)
    if match:
        return int(match.group(1))


@dataclass
class ASPA:
    customer: int
    providers: list[int]
    ta: Optional[str]

    @classmethod
    def from_dict(cls, d):
        try:
            if 'customer' in d:
                customer = parse_asn(d['customer'])
            elif 'customer_asid' in d:
                customer = parse_asn(d['customer_asid'])
            else:
                return None

            providers = list(map(parse_asn, d['providers']))
            return cls(customer, providers, d.get('ta'))
        except (KeyError, TypeError):
            return None


def parse_json(data: str) -> list[ASPA]:
    data = json.loads(data)
    return list(filter(None, map(ASPA.from_dict, data.get('aspas', []))))
