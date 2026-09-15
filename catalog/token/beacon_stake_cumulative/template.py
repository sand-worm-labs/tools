# Sandworm Power Toolbox — {{__tool_name}}
# The beacon chain deposit contract only exists on Ethereum mainnet, so this
# tool has no chain selector (unlike the rest of this EVM-agnostic catalog).
import json
from datetime import datetime

DATE_RANGE = """{{date_range}}"""

DEPOSIT_CONTRACT = "0x00000000219ab540356cBB839Cbe05303d7705Fa"

try:
    date_range = json.loads(DATE_RANGE)
    date_from = str(date_range["from"]).strip()
    date_to = str(date_range["to"]).strip()
    datetime.strptime(date_from, "%Y-%m-%d")
    datetime.strptime(date_to, "%Y-%m-%d")
except (json.JSONDecodeError, KeyError, ValueError):
    raise ValueError(f"Invalid date_range: {DATE_RANGE!r}")

deposit_hex = DEPOSIT_CONTRACT[2:].lower()

# Each successful deposit-contract transaction is treated as one validator
# deposit (the common case is exactly 32 ETH; top-up/partial deposits are
# rarer and still counted correctly by value, just not as a "new validator").
sql = f"""
with deposits as (
    select date_trunc('day', block_time) as day, value / 1e18 as amt
    from ethereum.transactions
    where "to" = from_hex('{deposit_hex}')
      and success = true
      and block_time >= date '{date_from}'
      and block_time < date '{date_to}' + interval '1' day
),
daily as (
    select day, sum(amt) as staked_amt, count(*) as validator_count
    from deposits
    group by day
)
select
    cast(day as date) as date,
    sum(staked_amt) over (order by day) as staked,
    sum(validator_count) over (order by day) as validators
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
