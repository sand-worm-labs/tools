# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
MIN_AMOUNT = "{{min_usd}}".strip() or "0"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
# Dune's raw-traces schema names BNB Chain "bnb", not "bsc".
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    min_amount_val = float(MIN_AMOUNT)
except ValueError:
    raise ValueError(f"Invalid min_usd: {MIN_AMOUNT!r}")
if min_amount_val < 0:
    raise ValueError(f"min_usd must be >= 0: {MIN_AMOUNT!r}")

schema = CHAIN_SCHEMA[CHAIN]
contract_hex = CONTRACT_ADDRESS[2:].lower()

# "Deposit" = a native-value call into the contract (e.g. an ETH deposit into
# a vault/staking contract), parsed straight from traces rather than an ERC20
# transfer event; min_usd is treated as a native-token-unit floor since no
# price join is applied here (no usd conversion for arbitrary trace values).
sql = f"""
with deposits as (
    select value / 1e18 as amount
    from {schema}.traces
    where "to" = from_hex('{contract_hex}')
      and value > 0
      and success = true
      and call_type = 'call'
),
filtered as (
    select amount from deposits where amount >= {min_amount_val}
),
bucketed as (
    select
        case
            when amount < 0.1 then '0-0.1'
            when amount < 1 then '0.1-1'
            when amount < 10 then '1-10'
            when amount < 100 then '10-100'
            when amount < 1000 then '100-1000'
            else '1000+'
        end as amount_range,
        amount
    from filtered
)
select
    amount_range,
    count(*) as deposit_count,
    sum(amount) as total_amount
from bucketed
group by amount_range
order by min(amount)
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
