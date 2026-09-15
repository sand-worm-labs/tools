# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
NATIVE_TOKEN = "{{native_token}}".strip().upper()
WALLET_ADDRESS = "{{wallet_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
# Raw per-chain schema prefixes for the trace tables (Dune spellbook names
# BSC's raw schema "bnb" and Avalanche's C-Chain schema "avalanche_c").
RAW_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
SYMBOL_RE = re.compile(r"^[A-Z0-9]{1,10}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not SYMBOL_RE.match(NATIVE_TOKEN):
    raise ValueError(f"Invalid native_token: {NATIVE_TOKEN!r}")
if not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")

raw_schema = RAW_SCHEMA[CHAIN]
wallet_hex = WALLET_ADDRESS[2:].lower()

sql = f"""
with native_movements as (
    select value as amt
    from {raw_schema}.traces
    where call_type = 'call'
      and success = true
      and "to" = from_hex('{wallet_hex}')
    union all
    select -value as amt
    from {raw_schema}.traces
    where call_type = 'call'
      and success = true
      and "from" = from_hex('{wallet_hex}')
),
balance as (
    select sum(amt) / 1e18 as balance
    from native_movements
),
latest_price as (
    select price as token_price
    from prices.usd
    where blockchain = '{CHAIN}'
      and symbol = '{NATIVE_TOKEN}'
    order by minute desc
    limit 1
)
select
    b.balance,
    coalesce(lp.token_price, 0) as token_price,
    b.balance * coalesce(lp.token_price, 0) as balance_usd
from balance b
left join latest_price lp on true
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
