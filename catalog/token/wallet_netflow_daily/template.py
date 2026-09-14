# Sandworm Power Toolbox — {{__tool_name}}
# "Transactions" here means native-coin (ETH-equivalent) value transfers, the
# closest EVM-native reading of the original description.
import re

WALLET_ADDRESS = "{{wallet_address}}"
DATE_FROM = "{{date_from}}".strip()
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Dune's raw <chain>.transactions schema names diverge from our chain keys for these two.
CHAIN_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

schema = CHAIN_SCHEMA[CHAIN]
wallet_hex = WALLET_ADDRESS[2:].lower()
date_where = f"and block_time >= date('{DATE_FROM}')" if DATE_FROM else ""

sql = f"""
with movements as (
    select block_time, value / 1e18 as amt, 1 as is_in
    from {schema}.transactions
    where "to" = from_hex('{wallet_hex}')
      and success
      {date_where}
    union all
    select block_time, value / 1e18 as amt, 0 as is_in
    from {schema}.transactions
    where "from" = from_hex('{wallet_hex}')
      and success
      {date_where}
)
select
    date_trunc('day', block_time) as day,
    sum(case when is_in = 1 then amt else 0 end) as inflow,
    sum(case when is_in = 0 then amt else 0 end) as outflow,
    sum(case when is_in = 1 then amt else -amt end) as netflow
from movements
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
