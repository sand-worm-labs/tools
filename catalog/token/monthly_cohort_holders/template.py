# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with first_seen as (
    select "to" as holder, min(date_trunc('month', block_time)) as first_month
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
    group by 1
),
monthly as (
    select first_month as month, count(*) as cohort_count
    from first_seen
    group by 1
)
select
    month,
    cohort_count,
    sum(cohort_count) over (order by month) as cumulative_holders
from monthly
order by month
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
