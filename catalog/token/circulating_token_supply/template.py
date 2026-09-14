# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
NON_CIRC_RAW = '''{{non_circ_addresses}}'''.replace("[", "").replace("]", "").replace('"', "")

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

non_circ = [a.strip() for a in NON_CIRC_RAW.split(",") if a.strip()]
for a in non_circ:
    if not ADDRESS_RE.match(a):
        raise ValueError(f"Invalid non_circ_addresses entry: {a!r}")
if not non_circ:
    non_circ = ["0x000000000000000000000000000000000000dEaD"]

contract_hex = CONTRACT_ADDRESS[2:].lower()
non_circ_hex_list = ", ".join(f"from_hex('{a[2:].lower()}')" for a in non_circ)

sql = f"""
with daily_mint_burn as (
    select
        date_trunc('day', block_time) as day,
        sum(case when "from" = from_hex('0000000000000000000000000000000000000000') then amount else 0 end) as minted,
        sum(case when "to" = from_hex('0000000000000000000000000000000000000000') then amount else 0 end) as burned
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
    group by 1
),
supply_running as (
    select day, sum(minted - burned) over (order by day) as total_supply
    from daily_mint_burn
),
non_circ_daily as (
    select
        date_trunc('day', block_time) as day,
        sum(case when "to" in ({non_circ_hex_list}) then amount else 0 end)
            - sum(case when "from" in ({non_circ_hex_list}) then amount else 0 end) as net
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
    group by 1
),
non_circ_running as (
    select day, sum(net) over (order by day) as non_circ_balance
    from non_circ_daily
)
select
    s.day,
    s.total_supply - coalesce(n.non_circ_balance, 0) as supply
from supply_running s
left join non_circ_running n on n.day = s.day
order by s.day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
