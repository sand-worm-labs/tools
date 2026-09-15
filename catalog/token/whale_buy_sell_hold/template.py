# Sandworm Power Toolbox — {{__tool_name}}
import re
from datetime import datetime

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DATE_FROM = "{{date_from}}"
MIN_USD = "{{min_usd}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    datetime.strptime(DATE_FROM, "%Y-%m-%d")
except ValueError:
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
try:
    min_usd_val = float(MIN_USD)
except ValueError:
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")
if min_usd_val < 0:
    raise ValueError(f"min_usd must be >= 0: {MIN_USD!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with trades as (
    select
        taker as address,
        case when token_bought_address = from_hex('{token_hex}') then amount_usd else 0 end as bought_usd,
        case when token_sold_address = from_hex('{token_hex}') then amount_usd else 0 end as sold_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{token_hex}') or token_sold_address = from_hex('{token_hex}'))
      and block_time >= date '{DATE_FROM}'
),
per_wallet as (
    select
        address,
        sum(bought_usd) as total_bought,
        sum(sold_usd) as total_sold
    from trades
    group by address
)
select
    to_hex(address) as address,
    total_bought,
    total_sold,
    total_bought - total_sold as net_hold
from per_wallet
where total_bought + total_sold >= {min_usd_val}
order by (total_bought + total_sold) desc
limit 200
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
