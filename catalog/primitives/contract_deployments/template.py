# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DEPLOYER = "{{deployer}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if DEPLOYER and not ADDRESS_RE.match(DEPLOYER):
    raise ValueError(f"Invalid deployer: {DEPLOYER!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

deployer_where = ""
if DEPLOYER:
    deployer_where = f"AND deployer = from_hex('{DEPLOYER[2:].lower()}')"

limit_clause = f"limit {LIMIT}" if LIMIT else ""

sql = f"""
select
    block_time,
    block_number,
    tx_hash,
    address as contract_address,
    deployer
from {CHAIN}.creation_traces
where 1 = 1
  {deployer_where}
  {{__time_where}}
order by block_time desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
