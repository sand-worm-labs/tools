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
WALLET_ADDRESS = "{{wallet_address}}".strip()
DATE_FROM, DATE_TO = _parse_date_range("""{{date_range}}""")

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if WALLET_ADDRESS and not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")

schema = CHAIN_SCHEMA[CHAIN]
date_from_clause = f"and block_time >= date('{DATE_FROM}')" if DATE_FROM else "and block_time >= now() - interval '30' day"
date_to_clause = f"and block_time <= date('{DATE_TO}')" if DATE_TO else ""
wallet_to_filter = f"and \"to\" = from_hex('{WALLET_ADDRESS[2:].lower()}')" if WALLET_ADDRESS else ""
wallet_from_filter = f"and \"from\" = from_hex('{WALLET_ADDRESS[2:].lower()}')" if WALLET_ADDRESS else ""

sql = f"""
with movements as (
    select "to" as wallet, date_trunc('day', block_time) as day, value / 1e18 as amt, 1 as is_in
    from {schema}.transactions
    where value > 0
      {date_from_clause} {date_to_clause}
      {wallet_to_filter}
    union all
    select "from" as wallet, date_trunc('day', block_time) as day, value / 1e18 as amt, 0 as is_in
    from {schema}.transactions
    where value > 0
      {date_from_clause} {date_to_clause}
      {wallet_from_filter}
)
select
    to_hex(wallet) as wallet_address,
    cast(day as date) as day,
    sum(case when is_in = 1 then amt else 0 end) as inflow,
    sum(case when is_in = 0 then amt else 0 end) as outflow,
    sum(case when is_in = 1 then amt else -amt end) as net
from movements
group by 1, 2
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
