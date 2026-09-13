# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
SCHEMA_UID = "{{schema_uid}}"
WALLET = "{{wallet}}"

ALLOWED_CHAINS = {"base", "optimism", "zksync", "linea"}
SCHEMA_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not SCHEMA_RE.match(SCHEMA_UID):
    raise ValueError(f"Invalid schema_uid: {SCHEMA_UID!r}")
if WALLET and not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")

wallet_where = f"and recipient = from_hex('{WALLET[2:].lower()}')" if WALLET else ""

# This table doesn't decode the attestation's raw event payload, so the
# score/stamp breakdown Gitcoin Passport encodes isn't available here — this
# returns attestation counts per recipient (re-attestation frequency) as a
# proxy, not a parsed score/stamp distribution.
sql = f"""
select
    '0x' || to_hex(recipient) as recipient,
    count(*) as attestation_count,
    min(evt_block_time) as first_attested,
    max(evt_block_time) as last_attested
from attestationstation_v1_multichain.eas_evt_attested
where chain = '{CHAIN}'
  and schema = from_hex('{SCHEMA_UID[2:].lower()}')
  {wallet_where}
group by recipient
order by attestation_count desc
limit 500
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.histogram({{__df_name}}, x="attestation_count")
fig.show()

{{__df_name}}
