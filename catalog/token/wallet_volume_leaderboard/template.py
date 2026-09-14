# Sandworm Power Toolbox — {{__tool_name}}
import re

PROTOCOL = "{{protocol}}".strip()
DATE_FROM = "{{date_from}}"
TOP_N = "{{top_n}}".strip()
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PROTOCOL_RE = re.compile(r"^[A-Za-z0-9_ .\-]{1,64}$")
# No universal "buy"/"sell" concept exists for an arbitrary swap; a trade is
# classified as a buy/sell of the non-stable side relative to a stablecoin.
STABLECOINS = {"USDC", "USDT", "DAI", "FDUSD", "TUSD", "USDe"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not PROTOCOL or not PROTOCOL_RE.match(PROTOCOL):
    raise ValueError(f"Invalid protocol: {PROTOCOL!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if TOP_N and not (TOP_N.isdigit() and int(TOP_N) > 0):
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

top_n = int(TOP_N) if TOP_N else 100
stable_list = ", ".join(f"'{s}'" for s in sorted(STABLECOINS))

sql = f"""
with trades as (
    select taker as wallet, amount_usd, token_bought_symbol, token_sold_symbol
    from dex.trades
    where blockchain = '{CHAIN}'
      and lower(project) = lower('{PROTOCOL}')
      and block_time >= date('{DATE_FROM}')
),
classified as (
    select
        wallet,
        amount_usd,
        case when token_sold_symbol in ({stable_list}) and token_bought_symbol not in ({stable_list}) then 1 else 0 end as is_buy,
        case when token_bought_symbol in ({stable_list}) and token_sold_symbol not in ({stable_list}) then 1 else 0 end as is_sell
    from trades
)
select
    '0x' || to_hex(wallet) as wallet,
    sum(amount_usd) as total_volume_usd,
    count(*) as daily_trades,
    sum(is_buy) as daily_buys,
    sum(is_sell) as daily_sells
from classified
group by wallet
order by total_volume_usd desc
limit {top_n}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
