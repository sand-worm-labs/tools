# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
AIRDROP_FROM = "{{airdrop_from}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not ADDRESS_RE.match(AIRDROP_FROM):
    raise ValueError(f"Invalid airdrop_from: {AIRDROP_FROM!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
airdrop_from_hex = AIRDROP_FROM[2:].lower()

sql = f"""
with recipients as (
    select distinct "to" as wallet, min(block_time) as received_at
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      and "from" = from_hex('{airdrop_from_hex}')
    group by "to"
),
outflows as (
    select distinct "from" as wallet
    from tokens.transfers t
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      and exists (
          select 1 from recipients r
          where r.wallet = t."from" and t.block_time > r.received_at
      )
)
select
    count(*) as total_wallets,
    count(*) filter (where o.wallet is null) as still_holding,
    100.0 * count(*) filter (where o.wallet is null) / nullif(count(*), 0) as retention_ratio
from recipients r
left join outflows o on o.wallet = r.wallet
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
