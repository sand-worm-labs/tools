# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DECIMALS = "{{decimals}}"
DAYS_LIMIT = "{{days_limit}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DECIMALS.isdigit():
    raise ValueError(f"Invalid decimals: {DECIMALS!r}")
if DAYS_LIMIT and not DAYS_LIMIT.isdigit():
    raise ValueError(f"Invalid days_limit: {DAYS_LIMIT!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
decimals_val = int(DECIMALS)
time_where = f"and block_time >= now() - interval '{DAYS_LIMIT}' day" if DAYS_LIMIT else ""

# Uses amount_raw / 10^decimals (user-supplied) instead of the pre-decoded
# `amount` column, so the result is correct even for tokens whose decimals
# tokens.erc20 metadata has missing or wrong.
sql = f"""
with daily as (
    select
        date_trunc('day', block_time) as day,
        sum(amount_raw / power(10, {decimals_val})) as daily_volume,
        count(*) as tx_count
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      {time_where}
    group by 1
)
select
    day,
    daily_volume,
    tx_count,
    sum(daily_volume) over (order by day) as cumulative_volume
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
