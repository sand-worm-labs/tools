# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()
MIN_PNL_USD = "{{min_pnl_usd}}".strip() or "1000"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
try:
    min_pnl = float(MIN_PNL_USD)
except ValueError:
    raise ValueError(f"Invalid min_pnl_usd: {MIN_PNL_USD!r}")

# "Early" = a wallet's first buy of a token happened within 24h of that
# token's first-ever trade on this chain in the lookback window. PnL is a
# simplified realized figure: USD received from sells minus USD spent on
# buys, per wallet per token, summed across tokens they bought early.
sql = f"""
with trades as (
    select
        block_time,
        taker,
        token_bought_address,
        token_sold_address,
        amount_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
token_inception as (
    select token_bought_address as token_address, min(block_time) as inception_time
    from trades
    group by 1
),
early_buys as (
    select distinct t.taker as wallet, t.token_bought_address as token_address
    from trades t
    join token_inception i on i.token_address = t.token_bought_address
    where t.block_time <= i.inception_time + interval '24' hour
),
wallet_token_flow as (
    select taker as wallet, token_bought_address as token_address, -amount_usd as flow_usd
    from trades
    union all
    select taker as wallet, token_sold_address as token_address, amount_usd as flow_usd
    from trades
),
wallet_pnl as (
    select wallet, token_address, sum(flow_usd) as net_pnl
    from wallet_token_flow
    group by 1, 2
)
select
    e.wallet,
    sum(p.net_pnl) as net_pnl,
    count(distinct e.token_address) as early_token_count,
    avg(case when p.net_pnl > 0 then 1.0 else 0.0 end) as win_rate
from early_buys e
join wallet_pnl p on p.wallet = e.wallet and p.token_address = e.token_address
group by e.wallet
having sum(p.net_pnl) >= {min_pnl}
order by net_pnl desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
