# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
EXCLUDE_ADDRESSES_RAW = '''{{exclude_addresses}}'''.replace("[", "").replace("]", "").replace('"', "")

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

exclude_addresses = [a.strip() for a in EXCLUDE_ADDRESSES_RAW.split(",") if a.strip()]
for a in exclude_addresses:
    if not ADDRESS_RE.match(a):
        raise ValueError(f"Invalid exclude_addresses entry: {a!r}")

# Dead/burn address always excluded from circulating supply, even if the caller didn't list it.
exclude_addresses = list({*exclude_addresses, "0x000000000000000000000000000000000000dEaD"})

contract_hex = CONTRACT_ADDRESS[2:].lower()
exclude_hex_list = ", ".join(f"from_hex('{a[2:].lower()}')" for a in exclude_addresses)

sql = f"""
with mints as (
    select sum(amount) as total_minted
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and "from" = from_hex('0000000000000000000000000000000000000000')
),
burns as (
    select sum(amount) as total_burned
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and "to" in ({exclude_hex_list}, from_hex('0000000000000000000000000000000000000000'))
),
excluded_inflow as (
    select sum(amount) as inflow
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and "to" in ({exclude_hex_list})
),
excluded_outflow as (
    select sum(amount) as outflow
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and "from" in ({exclude_hex_list})
)
select
    current_date as date,
    coalesce(m.total_minted, 0) - coalesce(b.total_burned, 0) as total_supply,
    coalesce(ei.inflow, 0) - coalesce(eo.outflow, 0) as excluded_balance,
    (coalesce(m.total_minted, 0) - coalesce(b.total_burned, 0))
        - (coalesce(ei.inflow, 0) - coalesce(eo.outflow, 0)) as circulating_supply
from mints m
cross join burns b
cross join excluded_inflow ei
cross join excluded_outflow eo
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
