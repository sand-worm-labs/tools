# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
MIN_USD = "{{min_usd}}".strip() or "0"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not MIN_USD.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 1:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

sql = f"""
with recent as (
    select token_bought_address as token, count(*) as txs, sum(amount_usd) as vol
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '1' day
      and amount_usd >= {MIN_USD}
    group by 1
),
historical as (
    select token_bought_address as token, sum(amount_usd) as vol
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
      and block_time < now() - interval '1' day
    group by 1
)
select
    to_hex(r.token) as token,
    r.txs as txs_last_24h,
    r.vol as vol_last_24h,
    r.vol / nullif(coalesce(h.vol, 0) / ({LOOKBACK_DAYS} - 1), 0) as awakening_score
from recent r
left join historical h on h.token = r.token
order by awakening_score desc nulls last
limit 200
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
