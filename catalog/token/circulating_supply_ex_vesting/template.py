# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_TO = "{{date_to}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if DATE_TO and not DATE_RE.match(DATE_TO):
    raise ValueError(f"Invalid date_to: {DATE_TO!r}")
# This tool is scoped to the Curve DAO token (CRV) and its veCRV vote-escrow
# lock, both of which are Ethereum mainnet-only deployments.
if CHAIN != "ethereum":
    raise ValueError("circulating_supply_ex_vesting only supports chain='ethereum' (CRV/veCRV are Ethereum mainnet-only)")

CRV_CONTRACT = "d533a949740bb3306d119cc777fa900ba034cd52"
VE_CRV_ESCROW = "5f3b5dfeb7b28cdbd7faba78963ee202a494e2a2"
cutoff_clause = f"and block_time <= timestamp '{DATE_TO}'" if DATE_TO else ""

sql = f"""
with mints as (
    select sum(amount) as total_minted
    from tokens.transfers
    where blockchain = 'ethereum'
      and token_standard = 'erc20'
      and contract_address = from_hex('{CRV_CONTRACT}')
      and "from" = from_hex('0000000000000000000000000000000000000000')
      {cutoff_clause}
),
burns as (
    select sum(amount) as total_burned
    from tokens.transfers
    where blockchain = 'ethereum'
      and token_standard = 'erc20'
      and contract_address = from_hex('{CRV_CONTRACT}')
      and "to" in (from_hex('0000000000000000000000000000000000000000'), from_hex('000000000000000000000000000000000000dead'))
      {cutoff_clause}
),
vested_inflow as (
    select sum(amount) as inflow
    from tokens.transfers
    where blockchain = 'ethereum'
      and token_standard = 'erc20'
      and contract_address = from_hex('{CRV_CONTRACT}')
      and "to" = from_hex('{VE_CRV_ESCROW}')
      {cutoff_clause}
),
vested_outflow as (
    select sum(amount) as outflow
    from tokens.transfers
    where blockchain = 'ethereum'
      and token_standard = 'erc20'
      and contract_address = from_hex('{CRV_CONTRACT}')
      and "from" = from_hex('{VE_CRV_ESCROW}')
      {cutoff_clause}
)
select
    (coalesce(m.total_minted, 0) - coalesce(b.total_burned, 0)) - (coalesce(vi.inflow, 0) - coalesce(vo.outflow, 0)) as circulating_supply,
    coalesce(m.total_minted, 0) - coalesce(b.total_burned, 0) as total_supply,
    coalesce(vi.inflow, 0) - coalesce(vo.outflow, 0) as vested_locked
from mints m
cross join burns b
cross join vested_inflow vi
cross join vested_outflow vo
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
