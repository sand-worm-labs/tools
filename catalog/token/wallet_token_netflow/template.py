# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
WALLET_ADDRESS = "{{wallet_address}}"
INTERVAL = "{{interval}}".strip() or "hour"
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
wallet_hex = WALLET_ADDRESS[2:].lower()

sql = f"""
with movements as (
    select date_trunc('{INTERVAL}', block_time) as period, amount as amt, 1 as is_in
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "to" = from_hex('{wallet_hex}')
    union all
    select date_trunc('{INTERVAL}', block_time) as period, amount as amt, 0 as is_in
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "from" = from_hex('{wallet_hex}')
)
select
    cast(period as varchar) as period,
    sum(case when is_in = 1 then amt else 0 end) as inflow,
    sum(case when is_in = 0 then amt else 0 end) as outflow,
    sum(case when is_in = 1 then amt else -amt end) as netflow
from movements
group by period
order by period
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
