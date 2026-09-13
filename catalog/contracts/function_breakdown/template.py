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

# Groups by raw 4-byte function selector rather than a resolved name — this
# tool covers every function a contract exposes at once, so it can't rely on
# the single-signature ABI lookup used by the primitives calldata decoder.
# Plain-value calls with no calldata (length 0) are bucketed separately as
# receive/fallback hits rather than dropped.
sql = f"""
select
    case when length(data) >= 4 then concat('0x', to_hex(substr(data, 1, 4))) else '(receive/fallback)' end as selector,
    count(*) as call_count,
    count(distinct "from") as unique_callers,
    round(100.0 * count(*) / sum(count(*)) over (), 2) as pct_of_calls
from {CHAIN}.transactions
where "to" = from_hex('{contract_hex}')
  {time_where}
group by 1
order by call_count desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="selector", y="call_count")
fig.show()

{{__df_name}}
