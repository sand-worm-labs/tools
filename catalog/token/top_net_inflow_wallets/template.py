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
CONTRACT_ADDRESS = "{{contract_address}}"
DATE_FROM, DATE_TO = _parse_date_range("""{{date_range}}""")

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
date_from_clause = f"and block_time >= date('{DATE_FROM}')" if DATE_FROM else ""
date_to_clause = f"and block_time <= date('{DATE_TO}')" if DATE_TO else ""

sql = f"""
with movements as (
    select taker as trader, amount_usd as amt, 'in' as direction
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address = from_hex('{contract_hex}')
      {date_from_clause} {date_to_clause}
    union all
    select taker as trader, amount_usd as amt, 'out' as direction
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_sold_address = from_hex('{contract_hex}')
      {date_from_clause} {date_to_clause}
)
select
    to_hex(trader) as trader_id,
    sum(case when direction = 'in' then amt else -amt end) as net_usd,
    sum(case when direction = 'in' then amt else 0 end) as inflow_usd,
    sum(case when direction = 'out' then amt else 0 end) as outflow_usd
from movements
group by 1
order by net_usd desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
