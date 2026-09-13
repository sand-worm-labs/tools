# Sandworm Power Toolbox — {{__tool_name}}
import re

WALLET = "{{wallet}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip() or "100"

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}

if not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

limit_clause = f"limit {LIMIT}" if LIMIT else ""
wallet_hex = WALLET[2:].lower()

# Curated, individually-verified subset (see volume/template.py) — Dune's
# bridges sector covers dozens more protocols per chain not included here.
DEPOSIT_TABLES = {
    "ethereum": ["across_v3_deposits", "synapse_rfq_deposits", "arbitrum_native_v1_deposits"],
    "optimism": ["across_v3_deposits", "synapse_rfq_deposits"],
    "arbitrum": ["across_v3_deposits", "synapse_rfq_deposits"],
    "base": ["across_v3_deposits", "synapse_rfq_deposits"],
    "polygon": ["across_v3_deposits"],
    "bnb": ["across_v3_deposits"],
}

pool_time_where = "" if DAYS == "all" else f"and block_time >= now() - interval '{DAYS}' day"
hop_days_where = "" if DAYS == "all" else f"and block_time >= now() - interval '{DAYS}' day"
op_days_where = "" if DAYS == "all" else f"and block_time >= now() - interval '{DAYS}' day"

union_parts = [
    f"select block_time, bridge_name, deposit_chain, withdrawal_chain, tx_hash "
    f"from bridges_{chain}.{t} "
    f"where (sender = from_hex('{wallet_hex}') or recipient = from_hex('{wallet_hex}')) {pool_time_where}"
    for chain, tables in DEPOSIT_TABLES.items()
    for t in tables
]
union_sql = "\nunion all\n".join(union_parts)

sql = f"""
with raw_activity as (
    {union_sql}
)
select block_time, bridge_name, deposit_chain as source_chain, withdrawal_chain as dest_chain, tx_hash
from raw_activity
union all
select block_time, 'Hop' as bridge_name, source_chain_name as source_chain, destination_chain_name as dest_chain, tx_hash
from hop_protocol.flows
where (sender = from_hex('{wallet_hex}') or receiver = from_hex('{wallet_hex}'))
  {hop_days_where}
union all
select block_time, 'Optimism Bridge' as bridge_name, source_chain_name as source_chain, destination_chain_name as dest_chain, tx_hash
from bridge_optimism.standard_bridge_flows
where (sender = from_hex('{wallet_hex}') or receiver = from_hex('{wallet_hex}'))
  {op_days_where}
order by block_time desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.histogram({{__df_name}}, x="bridge_name")
fig.show()

{{__df_name}}
