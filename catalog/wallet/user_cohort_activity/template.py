# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}"

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
ALLOWED_CHAINS = set(CHAIN_SCHEMA)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

schema = CHAIN_SCHEMA[CHAIN]

sql = f"""
with first_tx as (
    select "from" as wallet, min(block_time) as first_tx_time
    from {schema}.transactions
    where success
    group by 1
    having min(block_time) >= date '{DATE_FROM}'
),
cohort as (
    select wallet, date_trunc('month', first_tx_time) as block_date
    from first_tx
),
activity as (
    select
        c.block_date,
        c.wallet,
        count(*) as tx_count,
        sum(t.gas_used * t.gas_price) / 1e18 as eth_gas
    from {schema}.transactions t
    join cohort c on c.wallet = t."from"
    where t.success
    group by 1, 2
)
select
    block_date,
    count(distinct wallet) as user_count,
    avg(tx_count) as avg_tx_count,
    avg(eth_gas) as avg_gas
from activity
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
