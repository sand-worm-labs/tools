# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DAYS.isdigit() or int(DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {DAYS!r}")

sql = f"""
with first_in as (
    select
        "to" as recipient_address,
        min_by("from", block_time) as sender_address,
        min(block_time) as block_time,
        min_by(amount, block_time) as amount,
        min_by(tx_hash, block_time) as tx_hash
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
    group by "to"
)
select block_time, sender_address, recipient_address, amount, tx_hash
from first_in
where block_time >= now() - interval '{DAYS}' day
order by block_time desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
