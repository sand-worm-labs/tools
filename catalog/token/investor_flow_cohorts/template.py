# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
TO_ADDRESS = "{{to_address}}"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not ADDRESS_RE.match(TO_ADDRESS):
    raise ValueError(f"Invalid to_address: {TO_ADDRESS!r}")
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

schema = CHAIN_SCHEMA[CHAIN]
contract_hex = CONTRACT_ADDRESS[2:].lower()
to_hex_addr = TO_ADDRESS[2:].lower()
date_where = f"and t.block_time >= date('{DATE_FROM}')" if DATE_FROM else "and t.block_time >= now() - interval '90' day"

sql = f"""
with inflows as (
    select
        date_trunc('day', t.block_time) as day,
        t.amount * coalesce(p.price, 0) as amount_usd
    from tokens.transfers t
    left join prices.usd p
        on p.blockchain = '{schema}'
        and p.contract_address = t.contract_address
        and p.minute = date_trunc('minute', t.block_time)
    where t.blockchain = '{schema}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{contract_hex}')
      and t."to" = from_hex('{to_hex_addr}')
      {date_where}
),
cohorted as (
    select
        day,
        case
            when amount_usd >= 100000 then 'whale'
            when amount_usd >= 1000 then 'retail'
            else 'small'
        end as cohort,
        amount_usd
    from inflows
)
select
    day as date,
    cohort,
    count(*) as tx_count,
    sum(amount_usd) as total_inflow
from cohorted
group by day, cohort
order by day, cohort
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
