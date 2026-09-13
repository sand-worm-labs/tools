# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"
BOT_THRESHOLD = "{{bot_threshold}}".strip() or "100"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
if not BOT_THRESHOLD.isdigit() or int(BOT_THRESHOLD) <= 0:
    raise ValueError(f"Invalid bot_threshold: {BOT_THRESHOLD!r}")

# Fees reported in the chain's native gas token (gas_used * gas_price / 1e18),
# not USD.
sql = f"""
with daily_wallet as (
    select
        date_trunc('day', block_time) as day,
        "from" as wallet,
        count(*) as tx_count,
        sum(gas_used * gas_price) as fees_wei
    from {CHAIN}.transactions
    where block_time >= now() - interval '{LOOKBACK_DAYS}' day
      and success
    group by 1, 2
),
classified as (
    select
        day,
        wallet,
        tx_count,
        fees_wei,
        tx_count >= {BOT_THRESHOLD} as is_bot
    from daily_wallet
)
select
    day,
    sum(case when is_bot then fees_wei else 0 end) / 1e18 as bot_fees,
    sum(case when not is_bot then fees_wei else 0 end) / 1e18 as nonbot_fees,
    sum(case when is_bot then tx_count else 0 end) as bot_txs,
    sum(case when not is_bot then tx_count else 0 end) as nonbot_txs
from classified
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
