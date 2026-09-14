# Sandworm Power Toolbox — {{__tool_name}}

CHAIN = "{{chain}}"
START = "{{start}}"
END = "{{end}}"
LOOKBACK_DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not START.isdigit() or int(START) < 0:
    raise ValueError(f"Invalid start: {START!r}")
if not END.isdigit() or int(END) <= int(START):
    raise ValueError(f"Invalid end: {END!r} (must be > start)")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

scan_days = int(LOOKBACK_DAYS) * 3

# A token counts as "newly launched" only if its earliest trade across the
# wider scan window falls inside the requested lookback window (a cheap
# proxy for "first trade ever", since scanning dex.trades unbounded is too
# costly).
sql = f"""
with launches as (
    select token_bought_address as token, min(block_time) as launch_time
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{scan_days}' day
    group by 1
    having min(block_time) >= now() - interval '{LOOKBACK_DAYS}' day
),
windows as (
    select l.token, l.launch_time, t.block_time, t.amount_usd
    from launches l
    join dex.trades t
        on t.blockchain = '{CHAIN}'
        and t.token_bought_address = l.token
        and t.block_time < l.launch_time + interval '{END}' day
),
agg as (
    select
        token,
        launch_time,
        sum(case when block_time < launch_time + interval '{START}' day then amount_usd else 0 end) as baseline_volume,
        sum(case when block_time >= launch_time + interval '{START}' day then amount_usd else 0 end) as spike_volume
    from windows
    group by 1, 2
)
select
    '0x' || to_hex(token) as token,
    launch_time,
    baseline_volume,
    spike_volume,
    spike_volume / nullif(baseline_volume, 0) as spike_ratio
from agg
order by spike_ratio desc nulls last
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
