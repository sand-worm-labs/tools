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


CONTRACT_ADDRESS = "{{contract_address}}".strip()
CHAIN = "{{chain}}"
DATE_FROM, DATE_TO = _parse_date_range("""{{date_range}}""")

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
date_from_clause = f"and block_time >= date('{DATE_FROM}')" if DATE_FROM else "and block_time >= now() - interval '90' day"
date_to_clause = f"and block_time <= date('{DATE_TO}')" if DATE_TO else ""

sql = f"""
with trades as (
    select
        block_time,
        amount_usd,
        case when token_bought_address = from_hex('{token_hex}') then 'buy' else 'sell' end as side
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{token_hex}') or token_sold_address = from_hex('{token_hex}'))
      {date_from_clause} {date_to_clause}
)
select
    cast(date_trunc('day', block_time) as date) as day,
    sum(amount_usd) filter (where side = 'buy') as buy_usd,
    sum(amount_usd) filter (where side = 'sell') as sell_usd,
    sum(case when side = 'buy' then amount_usd else -amount_usd end) as net_usd
from trades
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
