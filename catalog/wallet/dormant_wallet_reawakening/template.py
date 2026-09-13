# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

# prior_tx looks across a wallet's full history (not just the lookback
# window) so the dormancy gap before its reawakening is measured correctly.
sql = f"""
with recent_actives as (
    select distinct "from" as wallet
    from {CHAIN}.transactions
    where block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
tx_history as (
    select
        t."from" as wallet,
        t.block_time,
        lag(t.block_time) over (partition by t."from" order by t.block_time) as prev_block_time
    from {CHAIN}.transactions t
    join recent_actives r on r.wallet = t."from"
),
gaps as (
    select
        wallet,
        max(block_time) as latest_tx,
        max(case when block_time >= now() - interval '{LOOKBACK_DAYS}' day then prev_block_time end) as prior_tx
    from tx_history
    group by wallet
)
select
    '0x' || to_hex(wallet) as wallet,
    date_diff('day', prior_tx, latest_tx) as days_dormant
from gaps
where prior_tx is not null
  and date_diff('day', prior_tx, latest_tx) > 30
order by days_dormant desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
