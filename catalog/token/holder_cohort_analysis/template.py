# Sandworm Power Toolbox — {{__tool_name}}
import json
import re

CONTRACT_ADDRESSES_RAW = "{{contract_addresses}}".strip()
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")

try:
    parsed = json.loads(CONTRACT_ADDRESSES_RAW) if CONTRACT_ADDRESSES_RAW.startswith("[") else CONTRACT_ADDRESSES_RAW.split(",")
except (json.JSONDecodeError, ValueError):
    parsed = CONTRACT_ADDRESSES_RAW.split(",")
CONTRACT_ADDRESSES = [a.strip() for a in parsed if str(a).strip()]

if not CONTRACT_ADDRESSES:
    raise ValueError("contract_addresses is required")
for a in CONTRACT_ADDRESSES:
    if not ADDRESS_RE.match(a):
        raise ValueError(f"Invalid contract address: {a!r}")

address_values = ", ".join(f"from_hex('{a[2:].lower()}')" for a in CONTRACT_ADDRESSES)

sql = f"""
with transfers as (
    select block_time, "to" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address in ({address_values})
),
first_seen as (
    select wallet, min(date_trunc('week', block_time)) as first_week
    from transfers
    group by wallet
),
weekly_activity as (
    select distinct date_trunc('week', block_time) as week, wallet
    from transfers
),
classified as (
    select
        w.week,
        case when w.week = f.first_week then 'new' else 'repeat' end as wallet_type
    from weekly_activity w
    join first_seen f on f.wallet = w.wallet
)
select
    week,
    count(*) filter (where wallet_type = 'new') as new_wallets,
    count(*) filter (where wallet_type = 'repeat') as repeat_wallets,
    count(*) as total_wallets
from classified
group by week
order by week
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
