# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
MONTHS = "{{months}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not MONTHS.isdigit() or int(MONTHS) <= 0:
    raise ValueError(f"Invalid months: {MONTHS!r}")

sql = f"""
with first_tx as (
    select "from" as address, min(block_time) as first_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
    group by "from"
)
select date_trunc('month', first_time) as month, count(*) as new_users
from first_tx
where first_time >= now() - interval '{MONTHS}' month
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
