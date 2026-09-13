# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}"
MIN_TXS = "{{min_txs}}"

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
if not MIN_TXS.isdigit() or int(MIN_TXS) <= 0:
    raise ValueError(f"Invalid min_txs: {MIN_TXS!r}")

schema = CHAIN_SCHEMA[CHAIN]

sql = f"""
with user_contract as (
    select "from" as wallet, "to" as contract, count(*) as tx_count
    from {schema}.transactions
    where success
      and "to" is not null
      and block_time >= date '{DATE_FROM}'
    group by 1, 2
),
user_contract_totals as (
    select wallet, count(distinct contract) as contract_count
    from user_contract
    group by 1
),
exclusive as (
    select uc.contract, uc.wallet, uc.tx_count
    from user_contract uc
    join user_contract_totals t on t.wallet = uc.wallet and t.contract_count = 1
    where uc.tx_count >= {MIN_TXS}
)
select
    to_hex(contract) as contract,
    count(distinct wallet) as loyal_users,
    sum(tx_count) as total_txs
from exclusive
group by 1
order by loyal_users desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
