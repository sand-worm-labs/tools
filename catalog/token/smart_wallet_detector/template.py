# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"
MIN_USD = "{{min_usd}}".strip() or "100"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
try:
    min_usd = float(MIN_USD)
except ValueError:
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")

sql = f"""
select
    taker as wallet_address,
    sum(amount_usd) as total_volume_30d,
    count(distinct token_bought_address) as unique_tokens_bought,
    count(distinct date_trunc('day', block_time)) as active_days
from dex.trades
where blockchain = '{CHAIN}'
  and block_time >= now() - interval '{LOOKBACK_DAYS}' day
  and amount_usd >= {min_usd}
group by taker
order by total_volume_30d desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
