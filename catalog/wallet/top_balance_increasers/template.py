# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}"
TOP_N = "{{top_n}}"

CHAIN_SCHEMA = {
    "ethereum": "ethereum",
    "base": "base",
    "optimism": "optimism",
    "arbitrum": "arbitrum",
    "polygon": "polygon",
    "bsc": "bnb",
    "avalanche": "avalanche_c",
    "celo": "celo",
}
# "SOL balance change" in the original description is treated as a stand-in
# for native-gas-token balance change on the selected EVM chain.
EXPLORERS = {
    "ethereum": "https://etherscan.io/address/",
    "base": "https://basescan.org/address/",
    "optimism": "https://optimistic.etherscan.io/address/",
    "arbitrum": "https://arbiscan.io/address/",
    "polygon": "https://polygonscan.com/address/",
    "bsc": "https://bscscan.com/address/",
    "avalanche": "https://snowtrace.io/address/",
    "celo": "https://celoscan.io/address/",
}
ALLOWED_CHAINS = set(CHAIN_SCHEMA)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if not TOP_N.isdigit() or int(TOP_N) <= 0:
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

schema = CHAIN_SCHEMA[CHAIN]
explorer = EXPLORERS[CHAIN]

sql = f"""
with received as (
    select "to" as address, sum(value) as amt
    from {schema}.traces
    where success
      and value > 0
      and block_time >= date '{DATE_FROM}'
    group by 1
),
sent as (
    select "from" as address, sum(value) as amt
    from {schema}.traces
    where success
      and value > 0
      and block_time >= date '{DATE_FROM}'
    group by 1
),
gas_paid as (
    select "from" as address, sum(gas_used * gas_price) as gas_amt
    from {schema}.transactions
    where block_time >= date '{DATE_FROM}'
    group by 1
),
net as (
    select
        coalesce(r.address, s.address, g.address) as address,
        coalesce(r.amt, 0) - coalesce(s.amt, 0) - coalesce(g.gas_amt, 0) as balance_change_wei
    from received r
    full outer join sent s on s.address = r.address
    full outer join gas_paid g on g.address = coalesce(r.address, s.address)
)
select
    to_hex(address) as address,
    balance_change_wei / 1e18 as balance_change,
    concat('{explorer}', to_hex(address)) as link
from net
where balance_change_wei > 0
order by balance_change_wei desc
limit {TOP_N}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
