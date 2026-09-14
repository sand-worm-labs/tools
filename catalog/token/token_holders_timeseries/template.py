# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# daily_holders is a live snapshot (wallets whose cumulative net balance is
# currently positive), unlike cumulative_holders which only ever grows (any
# wallet that has ever crossed into positive balance stays counted).
sql = f"""
with movements as (
    select date_trunc('day', block_time) as day, "to" as wallet, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select date_trunc('day', block_time) as day, "from" as wallet, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
),
wallet_daily as (
    select wallet, day, sum(amt) as day_change
    from movements
    group by wallet, day
),
wallet_running as (
    select
        wallet,
        day,
        sum(day_change) over (partition by wallet order by day) as running_balance,
        sum(day_change) over (partition by wallet order by day rows between unbounded preceding and 1 preceding) as prior_balance
    from wallet_daily
),
daily_counts as (
    select
        day,
        count(distinct wallet) filter (where running_balance > 0) as daily_holders,
        count(distinct wallet) filter (where running_balance > 0 and coalesce(prior_balance, 0) <= 0) as new_holders
    from wallet_running
    group by day
)
select
    day as date,
    daily_holders,
    sum(new_holders) over (order by day) as cumulative_holders
from daily_counts
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
