# Sandworm Power Toolbox — {{__tool_name}}
# EVM reinterpretation: original spec referenced Solana's dex_solana.trades;
# this catalog is EVM-only, so we use the Spellbook's chain-agnostic dex.trades.
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
INTERVAL = "{{interval}}"
THRESHOLD_USD = "{{threshold_usd}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")
try:
    threshold_usd_val = float(THRESHOLD_USD)
except ValueError:
    raise ValueError(f"Invalid threshold_usd: {THRESHOLD_USD!r}")
if threshold_usd_val < 0:
    raise ValueError(f"threshold_usd must be >= 0: {THRESHOLD_USD!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with trades as (
    select
        date_trunc('{INTERVAL}', block_time) as date,
        case when amount_usd >= {threshold_usd_val} then 'whale' else 'retail' end as user_type,
        case when token_bought_address = from_hex('{token_hex}') then amount_usd else 0 end as buy_usd,
        case when token_sold_address = from_hex('{token_hex}') then amount_usd else 0 end as sell_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{token_hex}') or token_sold_address = from_hex('{token_hex}'))
      and amount_usd is not null
)
select
    date,
    user_type,
    sum(buy_usd) as buy_volume,
    sum(sell_usd) as sell_volume
from trades
group by date, user_type
order by date desc, user_type
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
