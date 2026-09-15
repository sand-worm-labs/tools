# Sandworm Power Toolbox — {{__tool_name}}
import json
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
PROTOCOL = "{{protocol}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
PROTOCOL_RE = re.compile(r"^[A-Za-z0-9_ .\-]{1,64}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if PROTOCOL and not PROTOCOL_RE.match(PROTOCOL):
    raise ValueError(f"Invalid protocol: {PROTOCOL!r}")

try:
    date_range = json.loads("""{{date_range}}""")
    date_from = date_range.get("from")
    date_to = date_range.get("to")
except (json.JSONDecodeError, AttributeError, TypeError):
    raise ValueError("Invalid date_range: expected JSON object with from/to")
if not date_from or not date_to:
    raise ValueError("date_range requires both from and to")

token_hex = CONTRACT_ADDRESS[2:].lower()
protocol_where = f"and lower(project) = lower('{PROTOCOL}')" if PROTOCOL else ""

sql = f"""
with trades as (
    select
        taker,
        amount_usd,
        case when token_bought_address = from_hex('{token_hex}') then 1 else 0 end as is_buy,
        case when token_sold_address = from_hex('{token_hex}') then 1 else 0 end as is_sell
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{token_hex}') or token_sold_address = from_hex('{token_hex}'))
      and block_time >= date('{date_from}')
      and block_time <= date('{date_to}')
      {protocol_where}
)
select
    count(*) as trades,
    sum(is_buy) as buys,
    sum(is_sell) as sells,
    count(distinct taker) as traders,
    count(distinct taker) filter (where is_buy = 1) as buyers,
    count(distinct taker) filter (where is_sell = 1) as sellers,
    sum(amount_usd) as volume,
    sum(amount_usd) filter (where is_buy = 1) as buy_volume,
    sum(amount_usd) filter (where is_sell = 1) as sell_volume
from trades
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
