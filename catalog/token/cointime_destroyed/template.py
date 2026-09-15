# Sandworm Power Toolbox — {{__tool_name}}
# ERC20 is account-based (no UTXOs), so "coin-days destroyed" is approximated
# per wallet: for each outbound transfer, age = time since that wallet's
# previous transfer (in or out), coin-time destroyed = amount * age_in_days.
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

lookback_days = int(LOOKBACK_DAYS)
context_days = lookback_days * 2
contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with all_txns as (
    select "to" as wallet, block_time, amount, 0 as is_out
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= now() - interval '{context_days}' day
    union all
    select "from" as wallet, block_time, amount, 1 as is_out
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= now() - interval '{context_days}' day
),
with_lag as (
    select
        wallet,
        block_time,
        amount,
        is_out,
        lag(block_time) over (partition by wallet order by block_time) as prev_time
    from all_txns
),
destroyed as (
    select
        date_trunc('day', block_time) as day,
        amount * date_diff('second', prev_time, block_time) / 86400.0 as ctd
    from with_lag
    where is_out = 1
      and prev_time is not null
      and block_time >= now() - interval '{lookback_days}' day
)
select
    cast(day as date) as day,
    sum(ctd) as ctd
from destroyed
group by day
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
