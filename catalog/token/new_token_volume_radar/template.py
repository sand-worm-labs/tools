# Sandworm Power Toolbox — {{__tool_name}}

CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}"
MIN_USD = "{{min_usd}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
if not MIN_USD.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")

scan_days = int(LOOKBACK_DAYS) * 3

# A token counts as "new" only if its earliest trade across the wider scan
# window falls inside the requested lookback window (a cheap proxy for
# "first trade ever", since scanning dex.trades unbounded is too costly).
sql = f"""
with candidates as (
    select token_bought_address as token_address, min(block_time) as first_seen
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{scan_days}' day
    group by 1
    having min(block_time) >= now() - interval '{LOOKBACK_DAYS}' day
),
vol as (
    select c.token_address, c.first_seen, sum(t.amount_usd) as volume
    from candidates c
    join dex.trades t
        on t.blockchain = '{CHAIN}'
        and t.token_bought_address = c.token_address
        and t.block_time >= now() - interval '{scan_days}' day
    group by 1, 2
)
select
    '0x' || to_hex(token_address) as token_address,
    first_seen,
    volume,
    rank() over (order by volume desc) as rank
from vol
where volume >= {MIN_USD}
order by rank
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
