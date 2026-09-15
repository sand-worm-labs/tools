# Sandworm Power Toolbox — {{__tool_name}}
# "Native SOL transfers" reinterpreted generically as native-gas-token
# transfers on the selected EVM chain (value moved via CALL traces), since
# this catalog is EVM-only. A sybil "star" pattern is a single funder wallet
# fanning out near-identical small amounts to many distinct fresh wallets in
# a short window — the classic sybil-funding topology, here detected via a
# high receiver count combined with a low coefficient of variation in the
# amounts sent. `min_usd` is applied as a native-token amount threshold
# (not a USD price join) since no verifiable USD price feed exists for raw
# native transfers in the available tables.
import json

CHAIN = "{{chain}}"
MIN_USD = "{{min_usd}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
RAW_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")

try:
    min_usd_val = float(MIN_USD) if MIN_USD else 0.001
except ValueError:
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")
if min_usd_val < 0:
    raise ValueError(f"min_usd must be >= 0: {MIN_USD!r}")

try:
    date_range = json.loads("""{{date_range}}""")
    date_from = date_range.get("from")
    date_to = date_range.get("to")
except (json.JSONDecodeError, AttributeError, TypeError):
    raise ValueError("Invalid date_range: expected JSON object with from/to")
if not date_from or not date_to:
    raise ValueError("date_range requires both from and to")

raw_schema = RAW_SCHEMA[CHAIN]

sql = f"""
with transfers as (
    select "from" as sender, "to" as receiver, value / 1e18 as amount_native
    from {raw_schema}.traces
    where call_type = 'call'
      and success = true
      and value > 0
      and block_time >= date('{date_from}')
      and block_time <= date('{date_to}')
      and value / 1e18 >= {min_usd_val}
),
by_sender as (
    select
        sender,
        count(distinct receiver) as receiver_count,
        avg(amount_native) as avg_amount,
        stddev(amount_native) as amount_stddev
    from transfers
    group by sender
)
select
    to_hex(sender) as sender,
    receiver_count,
    receiver_count / (1 + coalesce(amount_stddev, 0) / nullif(avg_amount, 0)) as sybil_score,
    (receiver_count >= 10 and coalesce(amount_stddev, 0) / nullif(avg_amount, 0) < 0.2) as suspicious
from by_sender
where receiver_count >= 3
order by sybil_score desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
