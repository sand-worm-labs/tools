# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
RECIPIENT_ADDRESS = "{{recipient_address}}"
LIMIT = "{{limit}}".strip() or "100"

ALLOWED_CHAINS = {"base", "optimism", "zksync", "linea"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(RECIPIENT_ADDRESS):
    raise ValueError(f"Invalid recipient_address: {RECIPIENT_ADDRESS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

limit_clause = f"limit {LIMIT}" if LIMIT else ""

sql = f"""
select
    evt_block_time as block_time,
    '0x' || to_hex(schema) as schema_uid,
    '0x' || to_hex(attester) as attester,
    '0x' || to_hex(uid) as attestation_uid
from attestationstation_v1_multichain.eas_evt_attested
where chain = '{CHAIN}'
  and recipient = from_hex('{RECIPIENT_ADDRESS[2:].lower()}')
order by evt_block_time desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.histogram({{__df_name}}, x="schema_uid")
fig.show()

{{__df_name}}
