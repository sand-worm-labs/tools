# Sandworm Power Toolbox — {{__tool_name}}
# g5 originally cited a Solana DEX table; this catalog is EVM-only, so trades
# come from Dune's chain-agnostic dex.trades spellbook table.
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
TOP_N = "{{top_n}}".strip()
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not TOP_N.isdigit() or int(TOP_N) <= 0:
    raise ValueError(f"Invalid top_n: {TOP_N!r}")
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
top_n_val = int(TOP_N)
date_filter = f"and block_time >= date('{DATE_FROM}')" if DATE_FROM else ""

sql = f"""
with trades as (
    select date_trunc('hour', block_time) as hour, taker as trader, amount_usd as amt
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{token_hex}') or token_sold_address = from_hex('{token_hex}'))
      {date_filter}
),
hourly as (
    select hour, trader, sum(amt) as volume
    from trades
    group by hour, trader
),
ranked as (
    select hour, trader, volume, row_number() over (partition by hour order by volume desc) as rank
    from hourly
)
select hour, trader, volume, rank
from ranked
where rank <= {top_n_val}
order by hour desc, rank
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
