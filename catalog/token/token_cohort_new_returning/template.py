# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}".strip()
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "90"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# "Solana transfers" in the original description is reinterpreted as this
# catalog's EVM equivalent: ERC20 transfer events for the token contract.
sql = f"""
with all_events as (
    select "to" as user_address, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{token_hex}')
    union all
    select "from" as user_address, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{token_hex}')
),
first_seen as (
    select user_address, min(date_trunc('week', block_time)) as first_week
    from all_events
    group by user_address
),
activity as (
    select distinct user_address, date_trunc('week', block_time) as week
    from all_events
    where block_time >= now() - interval '{LOOKBACK_DAYS}' day
)
select
    a.week,
    count(distinct case when a.week = f.first_week then a.user_address end) as new_users,
    count(distinct case when a.week > f.first_week then a.user_address end) as returning_users,
    count(distinct a.user_address) as total_users
from activity a
join first_seen f on f.user_address = a.user_address
group by a.week
order by a.week
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
