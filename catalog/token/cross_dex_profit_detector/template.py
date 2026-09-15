# Sandworm Power Toolbox — {{__tool_name}}
# "pump.fun buys to pumpswap sells" (Solana-only venues) generalized to any
# EVM chain: buy on one DEX project, sell the same token on a different one.
CHAIN = "{{chain}}"
MIN_PROFIT_MULT = "{{min_profit_mult}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
try:
    min_profit_mult = float(MIN_PROFIT_MULT)
except ValueError:
    raise ValueError(f"Invalid min_profit_mult: {MIN_PROFIT_MULT!r}")
if min_profit_mult <= 1:
    raise ValueError("min_profit_mult must be > 1")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

lookback_days = int(LOOKBACK_DAYS)

sql = f"""
with buys as (
    select
        taker as wallet,
        token_bought_address as token,
        project as buy_project,
        amount_usd as buy_usd,
        block_time,
        row_number() over (partition by taker, token_bought_address order by block_time asc) as rn
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{lookback_days}' day
),
initial_buy as (
    select wallet, token, buy_project, buy_usd
    from buys
    where rn = 1
),
sells_agg as (
    select taker as wallet, token_sold_address as token, sum(amount_usd) as total_sell_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{lookback_days}' day
    group by taker, token_sold_address
),
cross_dex_flag as (
    select distinct s.taker as wallet, s.token_sold_address as token
    from dex.trades s
    join initial_buy ib on ib.wallet = s.taker and ib.token = s.token_sold_address
    where s.blockchain = '{CHAIN}'
      and s.block_time >= now() - interval '{lookback_days}' day
      and s.project <> ib.buy_project
),
combined as (
    select ib.wallet, ib.token, ib.buy_usd, sa.total_sell_usd
    from initial_buy ib
    join sells_agg sa on sa.wallet = ib.wallet and sa.token = ib.token
    join cross_dex_flag cd on cd.wallet = ib.wallet and cd.token = ib.token
    where ib.buy_usd > 0
)
select
    '0x' || to_hex(wallet) as wallet,
    total_sell_usd / buy_usd as profit_multiple,
    '0x' || to_hex(token) as token,
    least(1.0, (total_sell_usd / buy_usd) / ({min_profit_mult} * 10)) as confidence
from combined
where total_sell_usd / buy_usd >= {min_profit_mult}
order by profit_multiple desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
