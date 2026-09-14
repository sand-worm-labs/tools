# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}"
MIN_USD = "{{min_usd}}"
THRESHOLD_USD = "{{threshold_usd}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
if not MIN_USD.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")
if not THRESHOLD_USD.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid threshold_usd: {THRESHOLD_USD!r}")

# min_usd = minimum total token trading volume over the lookback window for a
# token to be considered ("emerging" enough to matter); threshold_usd =
# minimum cumulative USD one wallet must have bought of that token to count
# as a "whale".
sql = f"""
with buys as (
    select token_bought_address as token, taker, amount_usd
    from dex.trades
    where blockchain = '{CHAIN}' and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
token_totals as (
    select token, sum(amount_usd) as token_volume
    from buys
    group by 1
),
wallet_totals as (
    select token, taker, sum(amount_usd) as wallet_usd
    from buys
    group by 1, 2
),
whales as (
    select token, taker, wallet_usd
    from wallet_totals
    where wallet_usd >= {THRESHOLD_USD}
)
select
    to_hex(w.token) as token,
    count(distinct w.taker) as whale_count,
    sum(w.wallet_usd) as total_usd,
    sum(w.wallet_usd) / nullif(t.token_volume, 0) as whale_score
from whales w
join token_totals t on t.token = w.token
where t.token_volume >= {MIN_USD}
group by w.token, t.token_volume
order by whale_score desc
limit 200
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
