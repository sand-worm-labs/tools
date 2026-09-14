# Sandworm Power Toolbox — {{__tool_name}}
QUERY_ID = "{{query_id}}".strip()
DAYS_BACK = "{{days_back}}".strip()
MIN_COST_USD = "{{min_cost_usd}}".strip()
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not QUERY_ID.isdigit():
    raise ValueError(f"Invalid query_id: {QUERY_ID!r}")
if not DAYS_BACK.isdigit() or int(DAYS_BACK) <= 0:
    raise ValueError(f"Invalid days_back: {DAYS_BACK!r}")
try:
    min_cost_usd = float(MIN_COST_USD) if MIN_COST_USD else 1e-6
except ValueError:
    raise ValueError(f"Invalid min_cost_usd: {MIN_COST_USD!r}")
if min_cost_usd < 0:
    raise ValueError(f"Invalid min_cost_usd: {MIN_COST_USD!r}")

# query_id is assumed to point at another saved Dune query that returns
# (wallet_address, token_address) pairs — Dune's `query_<id>` syntax lets one
# query select from another query's materialized result. Win-rate/ROI/PNL use
# an average-cost-basis approximation per (wallet, token), not strict per-lot
# FIFO lot-matching, which Trino SQL cannot express without procedural code.
sql = f"""
with pairs as (
    select wallet_address, token_address
    from query_{QUERY_ID}
),
buys as (
    select
        t.taker as wallet,
        t.token_bought_address as token,
        sum(t.token_bought_amount) as buy_amt,
        sum(t.amount_usd) as buy_usd
    from dex.trades t
    join pairs p on t.taker = p.wallet_address and t.token_bought_address = p.token_address
    where t.blockchain = '{CHAIN}'
      and t.block_time >= now() - interval '{DAYS_BACK}' day
      and t.amount_usd >= {min_cost_usd}
    group by 1, 2
),
sells as (
    select
        t.taker as wallet,
        t.token_sold_address as token,
        t.amount_usd as sell_usd,
        t.amount_usd / nullif(t.token_sold_amount, 0) as sell_price
    from dex.trades t
    join pairs p on t.taker = p.wallet_address and t.token_sold_address = p.token_address
    where t.blockchain = '{CHAIN}'
      and t.block_time >= now() - interval '{DAYS_BACK}' day
      and t.amount_usd >= {min_cost_usd}
),
sells_scored as (
    select
        s.wallet,
        s.sell_usd,
        case when s.sell_price > (b.buy_usd / nullif(b.buy_amt, 0)) then 1 else 0 end as is_win
    from sells s
    left join buys b on b.wallet = s.wallet and b.token = s.token
),
per_wallet_sells as (
    select wallet, sum(sell_usd) as total_sell_usd, count(*) as sell_count, sum(is_win) as wins
    from sells_scored
    group by wallet
),
per_wallet_buys as (
    select wallet, sum(buy_usd) as total_buy_usd, count(*) as buy_count
    from buys
    group by wallet
)
select
    '0x' || to_hex(coalesce(b.wallet, s.wallet)) as wallet,
    case when s.sell_count > 0 then cast(s.wins as double) / s.sell_count else 0 end as winrate,
    case when b.total_buy_usd > 0 then (coalesce(s.total_sell_usd, 0) - b.total_buy_usd) / b.total_buy_usd else 0 end as roi,
    coalesce(s.total_sell_usd, 0) - coalesce(b.total_buy_usd, 0) as total_pnl,
    coalesce(b.buy_count, 0) + coalesce(s.sell_count, 0) as trade_count
from per_wallet_buys b
full outer join per_wallet_sells s on b.wallet = s.wallet
order by total_pnl desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
