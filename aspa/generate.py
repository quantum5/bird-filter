from aspa.data import ASPA


def generate_bird(aspas: list[ASPA]) -> str:
    lines = [
        'function is_aspa_invalid_pair(int upstream_asn; int downstream_asn) {',
        '    case downstream_asn {'
    ]

    for aspa in aspas:
        if aspa.providers:
            asns = ', '.join(map(str, aspa.providers))
            lines.append(f'        {aspa.customer}: if upstream_asn !~ [{asns}] then return true;')
        else:
            lines.append(f'        {aspa.customer}: return true;')

    lines += [
        '    }',
        '    return false;',
        '}'
    ]

    return '\n'.join(lines)
