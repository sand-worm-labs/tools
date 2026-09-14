# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
PROTOCOL = "{{protocol}}".strip().lower()
DATE_FROM = "{{date_from}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
PROTOCOL_RE = re.compile(r"^[a-z0-9_.]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not PROTOCOL_RE.match(PROTOCOL):
    raise ValueError(f"Invalid protocol: {PROTOCOL!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if not LOOKBACK_DAYS:
    LOOKBACK_DAYS = "7"
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

# EVM generalization: "graduation" (a pump.fun-style bonding-curve token
# migrating onto a DEX pool, a Solana-native concept) has no unified
# cross-chain attribution table in Spellbook, so a token's first-ever
# dex.trades appearance on this chain is used as its graduation event and
# labeled with the requested launchpad name.
sql = f"""
with first_trade as (
    select token_bought_address as token, min(date_trunc('day', block_time)) as day
    from dex.trades
    where blockchain = '{CHAIN}'
    group by token_bought_address
)
select day as date, '{PROTOCOL}' as platform, count(*) as graduates
from first_trade
where day >= date '{DATE_FROM}'
  and day < date '{DATE_FROM}' + interval '{LOOKBACK_DAYS}' day
group by day
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
