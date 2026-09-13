# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET_ADDRESS = "{{wallet_address}}".strip()
DATE_FROM = "{{date_from}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
NATIVE_SYMBOL = {"ethereum": "WETH", "base": "WETH", "optimism": "WETH", "arbitrum": "WETH", "polygon": "WMATIC", "bsc": "WBNB", "avalanche": "WAVAX", "celo": "CELO"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if WALLET_ADDRESS and not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]
native_symbol = NATIVE_SYMBOL[CHAIN]
wallet_filter = f"and \"from\" = from_hex('{WALLET_ADDRESS[2:].lower()}')" if WALLET_ADDRESS else ""

# bot_score is a simple heuristic (transactions-per-active-day relative to a
# 200 tx/day threshold, capped at 1.0) — not a calibrated ML classifier.
sql = f"""
with txs as (
    select
        to_hex("from") as wallet,
        date_trunc('day', block_time) as day,
        value / 1e18 as native_value
    from {schema}.transactions
    where block_time >= date('{DATE_FROM}')
      and block_time < date('{DATE_FROM}') + interval '{LOOKBACK_DAYS}' day
      {wallet_filter}
),
prices as (
    select date_trunc('day', minute) as day, avg(price) as price
    from prices.usd
    where blockchain = '{CHAIN}' and symbol = '{native_symbol}'
    group by 1
),
priced as (
    select t.wallet, t.day, t.native_value * coalesce(p.price, 0) as usd_value
    from txs t
    left join prices p on p.day = t.day
),
agg as (
    select
        wallet,
        count(*) as total_transactions,
        count(distinct day) as active_days,
        sum(usd_value) as total_volume_usd
    from priced
    group by 1
)
select
    wallet,
    total_transactions,
    active_days,
    total_volume_usd,
    least(1.0, total_transactions * 1.0 / (active_days * 200)) as bot_score
from agg
order by total_transactions desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
