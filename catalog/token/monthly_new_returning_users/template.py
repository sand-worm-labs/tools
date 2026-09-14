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

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with activity as (
    select date_trunc('month', block_time) as month, "from" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
    union all
    select date_trunc('month', block_time) as month, "to" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
),
monthly_users as (
    select distinct month, wallet from activity
),
first_seen as (
    select wallet, min(month) as first_month from monthly_users group by 1
)
select
    mu.month,
    count(distinct mu.wallet) as total_users,
    count(distinct case when fs.first_month = mu.month then mu.wallet end) as new_users,
    count(distinct case when fs.first_month <> mu.month then mu.wallet end) as returning_users
from monthly_users mu
join first_seen fs on fs.wallet = mu.wallet
group by mu.month
order by mu.month
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
