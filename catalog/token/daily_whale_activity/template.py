# Sandworm Power Toolbox — {{__tool_name}}
# "ETH transfer volume" reinterpreted generically as native-gas-token transfer
# volume on whichever EVM chain is selected, since this catalog is EVM-only.
import json

CHAIN = "{{chain}}"
THRESHOLD_ETH = "{{threshold_eth}}"
DATE_RANGE_RAW = """{{date_range}}""".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
# Dune's raw-traces schema names BNB Chain "bnb", not "bsc".
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
try:
    threshold_val = float(THRESHOLD_ETH)
except ValueError:
    raise ValueError(f"Invalid threshold_eth: {THRESHOLD_ETH!r}")
if threshold_val <= 0:
    raise ValueError(f"threshold_eth must be > 0: {THRESHOLD_ETH!r}")


def _parse_date_range(raw):
    if not raw:
        return None, None
    try:
        d = json.loads(raw)
        return d.get("from") or None, d.get("to") or None
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None, None


DATE_FROM, DATE_TO = _parse_date_range(DATE_RANGE_RAW)

schema = CHAIN_SCHEMA[CHAIN]
if DATE_FROM and DATE_TO:
    date_where = f"and block_time >= date('{DATE_FROM}') and block_time < date('{DATE_TO}') + interval '1' day"
else:
    date_where = "and block_time >= now() - interval '30' day"

sql = f"""
with amounts as (
    select date_trunc('day', block_time) as day, "from" as wallet, value / 1e18 as amt
    from {schema}.traces
    where call_type = 'call' and value > 0 and success = true
      {date_where}
    union all
    select date_trunc('day', block_time) as day, "to" as wallet, value / 1e18 as amt
    from {schema}.traces
    where call_type = 'call' and value > 0 and success = true
      {date_where}
),
daily_wallet as (
    select day, wallet, sum(amt) as eth_transferred, count(*) as transaction_count
    from amounts
    group by day, wallet
)
select
    day,
    concat('0x', to_hex(wallet)) as whale_address,
    eth_transferred,
    transaction_count
from daily_wallet
where eth_transferred >= {threshold_val}
order by day desc, eth_transferred desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
