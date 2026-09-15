# Sandworm Power Toolbox — {{__tool_name}}
# Generalized from "locked RDNT stakers" to any EVM staking/lock contract: a
# "staker" that week is any wallet that sent an ERC20 deposit to the contract.
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with deposits as (
    select date_trunc('week', block_time) as week, "from" as staker
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and "to" = from_hex('{contract_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
weekly as (
    select week, count(distinct staker) as locked_holders
    from deposits
    group by 1
)
select
    week,
    locked_holders,
    (locked_holders - lag(locked_holders) over (order by week)) * 100.0
        / nullif(lag(locked_holders) over (order by week), 0) as pct_change
from weekly
order by week
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
