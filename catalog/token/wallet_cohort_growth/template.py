# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
INTERVAL = "{{interval}}".strip() or "week"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with activity as (
    select "to" as wallet, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select "from" as wallet, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
),
periods as (
    select distinct wallet, date_trunc('{INTERVAL}', block_time) as period
    from activity
),
first_period as (
    select wallet, min(period) as first_period
    from periods
    group by wallet
)
select
    p.period as week,
    count(distinct case when p.period = f.first_period then p.wallet end) as new_wallets,
    count(distinct case when p.period > f.first_period then p.wallet end) as returning_wallets,
    count(distinct p.wallet) as total_wallets
from periods p
join first_period f on f.wallet = p.wallet
group by p.period
order by p.period
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
