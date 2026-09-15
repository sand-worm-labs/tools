# Sandworm Power Toolbox — {{__tool_name}}
import json
import re

CHAIN = "{{chain}}"
FACTORY_ADDRESS = "{{factory_address}}"
PROTOCOL = "{{protocol}}".strip()
DATE_RANGE = json.loads("""{{date_range}}""")

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
# Dune's raw-transactions/creation_traces schema names BNB Chain "bnb", not "bsc".
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LABEL_RE = re.compile(r"^[A-Za-z0-9_. -]{0,32}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(FACTORY_ADDRESS):
    raise ValueError(f"Invalid factory_address: {FACTORY_ADDRESS!r}")
if not LABEL_RE.match(PROTOCOL):
    raise ValueError(f"Invalid protocol label: {PROTOCOL!r}")

DATE_FROM, DATE_TO = str(DATE_RANGE.get("from", "")), str(DATE_RANGE.get("to", ""))
for label, value in (("date_range.from", DATE_FROM), ("date_range.to", DATE_TO)):
    if not DATE_RE.match(value):
        raise ValueError(f"Invalid {label}: {value!r}")
if DATE_FROM > DATE_TO:
    raise ValueError("date_range 'from' must not be after 'to'")

schema = CHAIN_SCHEMA[CHAIN]
factory_hex = FACTORY_ADDRESS[2:].lower()

# "pump.fun" (a Solana-only bonding-curve launchpad) generalized to any EVM
# launchpad factory contract: every token address the factory deploys counts
# as a "launch" for that day; `protocol` is a free-text label carried through
# for display only (the query itself is scoped by factory_address).
sql = f"""
with creations as (
    select block_time, address as token_address
    from {schema}.creation_traces
    where deployer = from_hex('{factory_hex}')
      and block_time >= date('{DATE_FROM}')
      and block_time < date('{DATE_TO}') + interval '1' day
)
select
    date_trunc('day', block_time) as date,
    count(distinct token_address) as daily_count,
    '{PROTOCOL}' as platform
from creations
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
