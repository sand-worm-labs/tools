# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
MIN_VALUE = "{{min_value}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not MIN_VALUE:
    MIN_VALUE = "0"
try:
    min_value_f = float(MIN_VALUE)
except ValueError:
    raise ValueError(f"Invalid min_value: {MIN_VALUE!r}")
if min_value_f < 0:
    raise ValueError(f"Invalid min_value: {MIN_VALUE!r}")

sql = f"""
with first_send as (
    select
        "to" as recipient_address,
        min_by("from", block_time) as from_address,
        min_by(contract_address, block_time) as contract_address,
        min(block_time) as block_time,
        min_by(amount, block_time) as amount
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
    group by "to"
),
priced as (
    select
        f.from_address,
        f.amount * coalesce(p.price, 0) as value_usd
    from first_send f
    left join prices.usd p on p.blockchain = '{CHAIN}'
        and p.contract_address = f.contract_address
        and p.minute = date_trunc('minute', f.block_time)
)
select from_address, count(*) as num_first_txs
from priced
where value_usd >= {min_value_f}
group by from_address
order by num_first_txs desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
