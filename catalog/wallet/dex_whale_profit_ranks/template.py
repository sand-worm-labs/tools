# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
MIN_USD = "{{min_usd}}".strip() or "100000"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
STABLECOINS = {"USDC", "USDT", "DAI", "FDUSD", "TUSD", "USDe"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
try:
    min_usd_val = float(MIN_USD)
except ValueError:
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")
if min_usd_val < 0:
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")

stable_list = ", ".join(f"'{s}'" for s in sorted(STABLECOINS))

# profit_usd is a realized-PnL proxy: net stablecoins received from selling
# minus stablecoins spent buying, not a true mark-to-market profit figure.
sql = f"""
with trades as (
    select
        taker,
        amount_usd,
        case when token_bought_symbol in ({stable_list}) then amount_usd else 0 end as stable_in,
        case when token_sold_symbol in ({stable_list}) then amount_usd else 0 end as stable_out
    from dex.trades
    where blockchain = '{CHAIN}'
      and amount_usd >= {min_usd_val}
)
select
    '0x' || to_hex(taker) as wallet,
    sum(amount_usd) as total_volume,
    count(*) as total_trades,
    sum(stable_in) - sum(stable_out) as profit_usd
from trades
group by taker
order by profit_usd desc
limit 100
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
