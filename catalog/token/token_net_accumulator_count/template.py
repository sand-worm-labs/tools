# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()
MIN_USD = "{{min_usd}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
STABLECOINS = "'USDC', 'USDT', 'DAI', 'FRAX', 'TUSD', 'USDP', 'LUSD'"

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
try:
    min_usd_val = float(MIN_USD)
except ValueError:
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")
if min_usd_val <= 0:
    raise ValueError(f"min_usd must be > 0: {MIN_USD!r}")

sql = f"""
with buys as (
    select
        taker,
        token_bought_address as token_address,
        token_bought_symbol as token_symbol,
        amount_usd as bought_usd,
        0 as sold_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
      and amount_usd >= {min_usd_val}
      and token_bought_symbol not in ({STABLECOINS})
),
sells as (
    select
        taker,
        token_sold_address as token_address,
        cast(null as varchar) as token_symbol,
        0 as bought_usd,
        amount_usd as sold_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
      and amount_usd >= {min_usd_val}
      and token_sold_symbol not in ({STABLECOINS})
),
unioned as (
    select * from buys
    union all
    select * from sells
),
per_trader as (
    select
        token_address,
        taker,
        max(token_symbol) as token_symbol,
        sum(bought_usd) - sum(sold_usd) as net_usd
    from unioned
    group by token_address, taker
)
select
    to_hex(token_address) as token_address,
    max(token_symbol) as token_symbol,
    count(*) filter (where net_usd > 0) as accumulator_count
from per_trader
group by token_address
order by accumulator_count desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
