# Sandworm Power Toolbox — {{__tool_name}}
# Original name/description referenced Solana "metadata programs"; there is no
# EVM equivalent, so this is reinterpreted as usage of a contract's callable
# methods, grouped by 4-byte function selector taken from raw calldata.
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
# Dune's raw <chain>.transactions schema names diverge from our chain keys for these two.
CHAIN_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if LOOKBACK_DAYS and not LOOKBACK_DAYS.isdigit():
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]
contract_hex = CONTRACT_ADDRESS[2:].lower()
time_where = f"and block_time >= now() - interval '{LOOKBACK_DAYS}' day" if LOOKBACK_DAYS else ""

sql = f"""
select
    substr(to_hex(data), 1, 8) as function_selector,
    min(date_trunc('day', block_time)) as inception_date,
    max(date_trunc('day', block_time)) as last_used_date,
    count(*) as call_count
from {schema}.transactions
where "to" = from_hex('{contract_hex}')
  and success = true
  and length(data) >= 4
  {time_where}
group by 1
order by call_count desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
