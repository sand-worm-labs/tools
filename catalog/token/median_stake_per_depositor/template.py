# Sandworm Power Toolbox — {{__tool_name}}
# The beacon chain deposit contract only exists on Ethereum mainnet, so this
# tool has no chain selector (unlike the rest of this EVM-agnostic catalog).
import re

DATE_FROM = "{{date_from}}".strip()
DEPOSIT_CONTRACT = "0x00000000219ab540356cBB839Cbe05303d7705Fa"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

deposit_hex = DEPOSIT_CONTRACT[2:].lower()

sql = f"""
with deposits as (
    select "from" as depositor, value / 1e18 as amount_eth
    from ethereum.transactions
    where "to" = from_hex('{deposit_hex}')
      and success = true
      and block_time >= date '{DATE_FROM}'
),
per_depositor as (
    select depositor, sum(amount_eth) as total_staked
    from deposits
    group by 1
)
select approx_percentile(total_staked, 0.5) as median
from per_depositor
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
