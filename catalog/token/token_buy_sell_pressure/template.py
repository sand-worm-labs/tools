# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

# No single token is specified for this tool, so buy/sell pressure is measured
# chain-wide: a trade that spends a stablecoin to acquire another token is
# "buy pressure" on risk assets, and a trade that dumps a token into a
# stablecoin is "sell pressure" — the standard proxy when no single token is
# targeted.
STABLECOINS = "'USDC', 'USDT', 'DAI', 'FRAX', 'TUSD', 'USDP', 'LUSD'"

sql = f"""
with trades as (
    select
        block_time,
        amount_usd,
        case
            when token_sold_symbol in ({STABLECOINS}) and token_bought_symbol not in ({STABLECOINS}) then 'buy'
            when token_bought_symbol in ({STABLECOINS}) and token_sold_symbol not in ({STABLECOINS}) then 'sell'
            else null
        end as side
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
)
select
    cast(date_trunc('day', block_time) as date) as day,
    sum(amount_usd) filter (where side = 'buy') as buy_volume,
    sum(amount_usd) filter (where side = 'sell') as sell_volume,
    sum(case when side = 'buy' then amount_usd when side = 'sell' then -amount_usd else 0 end) as net_pressure
from trades
where side is not null
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
