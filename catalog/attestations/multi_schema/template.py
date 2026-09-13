# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
SCHEMA_UIDS_RAW = "{{schema_uids}}".replace("[", "").replace("]", "").replace('"', "")
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"base", "optimism", "zksync", "linea"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
SCHEMA_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")

schema_uids = [s.strip() for s in SCHEMA_UIDS_RAW.split(",") if s.strip()]

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not schema_uids:
    raise ValueError("schema_uids is required")
for s in schema_uids:
    if not SCHEMA_RE.match(s):
        raise ValueError(f"Invalid schema_uid: {s!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

time_where = "" if DAYS == "all" else f"AND evt_block_time >= NOW() - INTERVAL '{DAYS}' DAY"
limit_clause = f"limit {LIMIT}" if LIMIT else ""
schema_in_sql = ", ".join(f"from_hex('{s[2:].lower()}')" for s in schema_uids)

sql = f"""
select
    evt_block_date as day,
    '0x' || to_hex(schema) as schema_uid,
    count(*) as attestation_count,
    count(distinct attester) as unique_attesters,
    count(distinct recipient) as unique_recipients
from attestationstation_v1_multichain.eas_evt_attested
where chain = '{CHAIN}'
  and schema in ({schema_in_sql})
  {time_where}
group by 1, 2
order by 1, 2
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y="attestation_count", color="schema_uid")
fig.show()

{{__df_name}}
