# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
MIN_ACTIVITY = "{{min_activity}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if MIN_ACTIVITY and (not MIN_ACTIVITY.isdigit() or int(MIN_ACTIVITY) < 1):
    raise ValueError(f"Invalid min_activity: {MIN_ACTIVITY!r}")
min_activity_val = int(MIN_ACTIVITY) if MIN_ACTIVITY else 1

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
per_wallet as (
    select
        wallet,
        min(date_trunc('day', block_time)) as first_seen_day,
        count(*) as total_activity
    from activity
    group by wallet
)
select
    to_hex(wallet) as wallet,
    first_seen_day,
    total_activity
from per_wallet
where total_activity >= {min_activity_val}
order by first_seen_day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
