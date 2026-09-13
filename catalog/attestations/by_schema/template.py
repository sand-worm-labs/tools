# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
SCHEMA_UID = "{{schema_uid}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"base", "optimism", "zksync", "linea"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
SCHEMA_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not SCHEMA_RE.match(SCHEMA_UID):
    raise ValueError(f"Invalid schema_uid: {SCHEMA_UID!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

time_where = "" if DAYS == "all" else f"AND evt_block_time >= NOW() - INTERVAL '{DAYS}' DAY"
limit_clause = f"limit {LIMIT}" if LIMIT else ""
schema_hex = SCHEMA_UID[2:].lower()

sql = f"""
with attested as (
    select evt_block_date as day, uid, attester, recipient
    from attestationstation_v1_multichain.eas_evt_attested
    where chain = '{CHAIN}'
      and schema = from_hex('{schema_hex}')
      {time_where}
),
revoked as (
    select uid
    from attestationstation_v1_multichain.eas_evt_revoked
    where chain = '{CHAIN}'
      and schema = from_hex('{schema_hex}')
)
select
    a.day,
    count(*) as attestation_count,
    count(distinct a.attester) as unique_attesters,
    count(distinct a.recipient) as unique_recipients,
    count(r.uid) as revoked_count
from attested a
left join revoked r on r.uid = a.uid
group by a.day
order by a.day
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y=["attestation_count", "unique_attesters", "unique_recipients"])
fig.show()

{{__df_name}}
