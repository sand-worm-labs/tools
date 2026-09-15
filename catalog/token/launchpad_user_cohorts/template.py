# Sandworm Power Toolbox — {{__tool_name}}
# EVM generalization: "creators on pump.fun-style launchpads" reinterpreted as the
# wallets whose transactions triggered an EVM factory contract to deploy a token
# (the tx sender behind the factory call, joined via tx_hash to creation_traces).
import re

CHAIN = "{{chain}}"
FACTORY_ADDRESS = "{{factory_address}}"
PROTOCOL = "{{protocol}}".strip() or "custom"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
PROTOCOL_RE = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(FACTORY_ADDRESS):
    raise ValueError(f"Invalid factory_address: {FACTORY_ADDRESS!r}")
if not PROTOCOL_RE.match(PROTOCOL):
    raise ValueError(f"Invalid protocol label: {PROTOCOL!r}")
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if not DATE_FROM:
    DATE_FROM = "2000-01-01"

schema = CHAIN_SCHEMA[CHAIN]
factory_hex = FACTORY_ADDRESS[2:].lower()

sql = f"""
with creator_activity as (
    select date_trunc('day', c.block_time) as day, t."from" as creator
    from {schema}.creation_traces c
    join {schema}.transactions t on t.hash = c.tx_hash
    where c.deployer = from_hex('{factory_hex}')
      and c.block_time >= date '{DATE_FROM}'
),
first_seen as (
    select creator, min(day) as first_day
    from creator_activity
    group by 1
),
daily as (
    select
        a.day,
        count(distinct a.creator) as active_users,
        count(distinct case when f.first_day = a.day then a.creator end) as new_users
    from creator_activity a
    join first_seen f on f.creator = a.creator
    group by a.day
)
select
    day as date,
    new_users,
    active_users,
    sum(new_users) over (order by day) as cumulative_users
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
