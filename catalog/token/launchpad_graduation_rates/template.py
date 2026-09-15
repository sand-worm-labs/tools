# Sandworm Power Toolbox — {{__tool_name}}
# EVM generalization: "graduation" (a pump.fun-style bonding-curve token migrating
# to a DEX pool, a Solana-only concept) is modeled as a factory-deployed ERC-20
# token's first-ever DEX trade on the same chain.
import re

CHAIN = "{{chain}}"
FACTORY_ADDRESS = "{{factory_address}}"
PROTOCOL = "{{protocol}}".strip() or "custom"
LOOKBACK_DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
PROTOCOL_RE = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(FACTORY_ADDRESS):
    raise ValueError(f"Invalid factory_address: {FACTORY_ADDRESS!r}")
if not PROTOCOL_RE.match(PROTOCOL):
    raise ValueError(f"Invalid protocol label: {PROTOCOL!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]
factory_hex = FACTORY_ADDRESS[2:].lower()

sql = f"""
with creations as (
    select date_trunc('day', block_time) as day, address as token_address
    from {schema}.creation_traces
    where deployer = from_hex('{factory_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
first_trade as (
    select token_bought_address as token_address, min(block_time) as graduated_at
    from dex.trades
    where blockchain = '{CHAIN}'
    group by 1
)
select
    c.day,
    '{PROTOCOL}' as platform,
    count(distinct c.token_address) as launched,
    count(distinct case when ft.graduated_at is not null then c.token_address end) as graduated,
    count(distinct case when ft.graduated_at is not null then c.token_address end) * 1.0
        / nullif(count(distinct c.token_address), 0) as graduation_rate
from creations c
left join first_trade ft on ft.token_address = c.token_address
group by c.day
order by c.day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
