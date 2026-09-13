# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
ATTESTOR_ADDRESS = "{{attestor_address}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"base", "optimism", "zksync", "linea"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(ATTESTOR_ADDRESS):
    raise ValueError(f"Invalid attestor_address: {ATTESTOR_ADDRESS!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

time_where = "" if DAYS == "all" else f"AND evt_block_time >= NOW() - INTERVAL '{DAYS}' DAY"
limit_clause = f"limit {LIMIT}" if LIMIT else ""

sql = f"""
select
    evt_block_date as day,
    '0x' || to_hex(schema) as schema_uid,
    count(*) as attestation_count,
    count(distinct recipient) as unique_recipients
from attestationstation_v1_multichain.eas_evt_attested
where chain = '{CHAIN}'
  and attester = from_hex('{ATTESTOR_ADDRESS[2:].lower()}')
  {time_where}
group by 1, 2
order by 1 desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="day", y="attestation_count", color="schema_uid")
fig.show()

{{__df_name}}
