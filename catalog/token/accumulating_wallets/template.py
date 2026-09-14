# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with trades as (
    select
        taker as trader,
        case when token_bought_address = from_hex('{contract_hex}') then amount_usd else 0 end as bought_usd,
        case when token_sold_address = from_hex('{contract_hex}') then amount_usd else 0 end as sold_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{contract_hex}') or token_sold_address = from_hex('{contract_hex}'))
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
)
select
    to_hex(trader) as trader,
    sum(bought_usd) as bought_usd,
    sum(sold_usd) as sold_usd,
    sum(bought_usd) - sum(sold_usd) as net_accumulation
from trades
group by trader
having sum(bought_usd) - sum(sold_usd) > 0
order by net_accumulation desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
