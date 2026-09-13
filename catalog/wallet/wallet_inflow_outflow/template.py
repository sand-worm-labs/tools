# Sandworm Power Toolbox — {{__tool_name}}
import json
import re


def _parse_date_range(raw):
    raw = raw.strip()
    if not raw:
        return None, None
    try:
        d = json.loads(raw)
        return d.get("from") or None, d.get("to") or None
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None, None


CHAIN = "{{chain}}"
WALLET_ADDRESS = "{{wallet_address}}"
DATE_FROM, DATE_TO = _parse_date_range("""{{date_range}}""")

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")

schema = CHAIN_SCHEMA[CHAIN]
wallet_hex = WALLET_ADDRESS[2:].lower()
date_from_clause = f"and block_time >= date('{DATE_FROM}')" if DATE_FROM else ""
date_to_clause = f"and block_time <= date('{DATE_TO}')" if DATE_TO else ""

sql = f"""
with movements as (
    select 'inflow' as type, value / 1e18 as amt
    from {schema}.transactions
    where "to" = from_hex('{wallet_hex}')
      and value > 0
      {date_from_clause} {date_to_clause}
    union all
    select 'outflow' as type, value / 1e18 as amt
    from {schema}.transactions
    where "from" = from_hex('{wallet_hex}')
      and value > 0
      {date_from_clause} {date_to_clause}
)
select type, count(*) as count, sum(amt) as sum_value
from movements
group by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
