# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
FACTORY_ADDRESS = "{{factory_address}}"
DAYS_LOOKBACK = "{{days_lookback}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(FACTORY_ADDRESS):
    raise ValueError(f"Invalid factory_address: {FACTORY_ADDRESS!r}")
if not DAYS_LOOKBACK.isdigit() or int(DAYS_LOOKBACK) <= 0:
    raise ValueError(f"Invalid days_lookback: {DAYS_LOOKBACK!r}")

schema = CHAIN_SCHEMA[CHAIN]
factory_hex = FACTORY_ADDRESS[2:].lower()

# Generalized from "pump.fun vs other platforms" (a Solana-only product) to
# "a given EVM launchpad factory contract vs every other newly created token
# contract on the same chain" — the closest EVM-native equivalent of
# comparing one bonding-curve platform's share of new token launches.
sql = f"""
with creations as (
    select block_time, address as token_address, deployer
    from {schema}.creation_traces
    where block_time >= now() - interval '{DAYS_LOOKBACK}' day
),
daily as (
    select
        date_trunc('day', block_time) as day,
        approx_distinct(case when deployer = from_hex('{factory_hex}') then token_address end) as factory_launches,
        approx_distinct(case when deployer != from_hex('{factory_hex}') then token_address end) as other_launches
    from creations
    group by 1
)
select
    day as date,
    factory_launches,
    other_launches,
    factory_launches * 1.0 / nullif(factory_launches + other_launches, 0) as factory_share
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
