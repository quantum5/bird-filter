from aspa.data import ASPA


def generate_bird(aspas: list[ASPA]) -> str:
    lines = [
        'function is_aspa_invalid_pair(int upstream_asn; int downstream_asn) {',
        '    case downstream_asn {'
    ]

    for aspa in aspas:
        if not aspa.providers:
            lines.append(f'        {aspa.customer}: return true;')
            continue

        lines.append(f'        {aspa.customer}: case upstream_asn {{')
        for provider in aspa.providers:
            lines.append(f'            {provider}: {{}}')

        lines += [
            '            else: return true;',
            '        }'
        ]

    lines += [
        '    }',
        '    return false;',
        '}'
    ]

    return '\n'.join(lines)
