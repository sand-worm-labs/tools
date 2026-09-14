# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}"
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# Realized PnL is approximated as: usd received from sells minus usd spent on
# buys (an average-cost-basis proxy, not strict per-lot FIFO). A sell "wins"
# when its execution price beats the wallet's own average buy price.
sql = f"""
with buys as (
    select taker as wallet, sum(token_bought_amount) as buy_amt, sum(amount_usd) as buy_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address = from_hex('{token_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
sells as (
    select
        taker as wallet,
        amount_usd as sell_usd,
        amount_usd / nullif(token_sold_amount, 0) as sell_price
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_sold_address = from_hex('{token_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
sells_scored as (
    select
        s.wallet,
        s.sell_usd,
        case when s.sell_price > (b.buy_usd / nullif(b.buy_amt, 0)) then 1 else 0 end as is_win
    from sells s
    left join buys b on b.wallet = s.wallet
),
sell_agg as (
    select wallet, sum(sell_usd) as total_sell_usd, count(*) as sell_count, sum(is_win) as wins
    from sells_scored
    group by wallet
)
select
    '0x' || to_hex(coalesce(b.wallet, sa.wallet)) as wallet,
    coalesce(sa.total_sell_usd, 0) - coalesce(b.buy_usd, 0) as pnl_usd,
    case when sa.sell_count > 0 then cast(sa.wins as double) / sa.sell_count else 0 end as win_rate,
    coalesce(b.buy_usd, 0) as buy_volume
from buys b
full outer join sell_agg sa on b.wallet = sa.wallet
order by pnl_usd desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
