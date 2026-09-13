# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}".strip()
TOP_N_WHALES = "{{top_n_whales}}".strip() or "10"
TOP_N_DESTS = "{{top_n_dests}}".strip() or "5"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if not TOP_N_WHALES.isdigit() or int(TOP_N_WHALES) <= 0:
    raise ValueError(f"Invalid top_n_whales: {TOP_N_WHALES!r}")
if not TOP_N_DESTS.isdigit() or int(TOP_N_DESTS) <= 0:
    raise ValueError(f"Invalid top_n_dests: {TOP_N_DESTS!r}")

schema = CHAIN_SCHEMA[CHAIN]

sql = f"""
with senders as (
    select "from" as wallet, sum(value) / 1e18 as total_sent
    from {schema}.transactions
    where block_time >= date('{DATE_FROM}')
      and value > 0
    group by 1
    order by total_sent desc
    limit {TOP_N_WHALES}
),
flows as (
    select t."from" as whale_from, t."to" as dest, sum(t.value) / 1e18 as total_value
    from {schema}.transactions t
    join senders s on s.wallet = t."from"
    where t.block_time >= date('{DATE_FROM}')
      and t.value > 0
    group by 1, 2
),
ranked as (
    select
        whale_from,
        dest,
        total_value,
        row_number() over (partition by whale_from order by total_value desc) as destination_rank
    from flows
)
select
    to_hex(whale_from) as whale_from,
    to_hex(dest) as top_to,
    total_value,
    destination_rank
from ranked
where destination_rank <= {TOP_N_DESTS}
order by whale_from, destination_rank
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
