# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
ORACLE_ADDRESS = "{{oracle_address}}"
LOOKBACK_HOURS = "{{lookback_hours}}".strip() or "1"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(ORACLE_ADDRESS):
    raise ValueError(f"Invalid oracle_address: {ORACLE_ADDRESS!r}")
if not (LOOKBACK_HOURS.isdigit() and int(LOOKBACK_HOURS) > 0):
    raise ValueError(f"Invalid lookback_hours: {LOOKBACK_HOURS!r}")

# "Compute units" here is gas used by transactions calling this oracle contract
# (e.g. Chainlink-style updateAnswer calls) — an EVM gas proxy, not a
# Solana-style compute-budget metric.
sql = f"""
select
    '{ORACLE_ADDRESS}' as oracle,
    avg(gas_used) as avg_cu_per_update,
    count(*) as update_count
from {CHAIN}.transactions
where "to" = from_hex('{ORACLE_ADDRESS[2:].lower()}')
  and block_time >= now() - interval '{LOOKBACK_HOURS}' hour
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
