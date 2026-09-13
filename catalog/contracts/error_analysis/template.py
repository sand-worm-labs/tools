# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS}' DAY"
limit_clause = f"limit {LIMIT}" if LIMIT else ""

# `error` on the raw traces table is only populated for calls that actually
# reverted/failed, so failed calls with no engine-reported reason fall into
# an explicit 'unknown' bucket rather than being dropped.
sql = f"""
select
    date_trunc('day', block_time) as day,
    coalesce(error, 'unknown') as error_reason,
    count(*) as failure_count,
    count(distinct "from") as unique_callers
from {CHAIN}.traces
where type = 'call'
  and success = false
  and "to" = from_hex('{contract_hex}')
  {time_where}
group by 1, 2
order by 1 desc, failure_count desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="day", y="failure_count", color="error_reason")
fig.show()

{{__df_name}}
