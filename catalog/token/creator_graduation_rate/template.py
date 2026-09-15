# Sandworm Power Toolbox — {{__tool_name}}
# "Pump.fun graduation" (a Solana-only concept) generalized to any EVM chain:
# a token "graduates" if it starts trading on a DEX within a grace window of
# its deployment.
from datetime import datetime

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
try:
    datetime.strptime(DATE_FROM, "%Y-%m-%d")
except ValueError:
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if LOOKBACK_DAYS and (not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

grace_days = int(LOOKBACK_DAYS) if LOOKBACK_DAYS else 30

sql = f"""
with created_tokens as (
    select tx."from" as creator, tx.contract_address as token_address, tx.block_time as launch_time
    from {CHAIN}.transactions tx
    join tokens.erc20 e on e.blockchain = '{CHAIN}' and e.contract_address = tx.contract_address
    where tx."to" is null
      and tx.success = true
      and tx.block_time >= date '{DATE_FROM}'
),
graduated as (
    select
        ct.creator,
        exists (
            select 1
            from dex.trades d
            where d.blockchain = '{CHAIN}'
              and (d.token_bought_address = ct.token_address or d.token_sold_address = ct.token_address)
              and d.block_time between ct.launch_time and ct.launch_time + interval '{grace_days}' day
        ) as is_graduated
    from created_tokens ct
),
per_creator as (
    select
        creator,
        count(*) as total_tokens,
        sum(case when is_graduated then 1 else 0 end) as graduated
    from graduated
    group by creator
)
select
    '0x' || to_hex(creator) as creator,
    total_tokens,
    graduated,
    100.0 * graduated / nullif(total_tokens, 0) as graduation_rate
from per_creator
order by graduation_rate desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
