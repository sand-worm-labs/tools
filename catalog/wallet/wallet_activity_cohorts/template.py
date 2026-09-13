# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

schema = CHAIN_SCHEMA[CHAIN]
contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with calls as (
    select date_trunc('day', block_time) as day, "from" as caller
    from {schema}.traces
    where "to" = from_hex('{contract_hex}')
      and success
      and block_time >= date('{DATE_FROM}')
    group by 1, 2
),
days as (
    select distinct day from calls
),
dau as (
    select day, count(distinct caller) as dau from calls group by 1
),
wau as (
    select d.day, count(distinct c.caller) as wau
    from days d
    join calls c on c.day > d.day - interval '7' day and c.day <= d.day
    group by 1
),
mau as (
    select d.day, count(distinct c.caller) as mau
    from days d
    join calls c on c.day > d.day - interval '30' day and c.day <= d.day
    group by 1
)
select
    dau.day as period,
    dau.dau,
    wau.wau,
    mau.mau
from dau
join wau on wau.day = dau.day
join mau on mau.day = dau.day
order by period
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
