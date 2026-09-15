# Sandworm Power Toolbox — {{__tool_name}}
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

token_hex = CONTRACT_ADDRESS[2:].lower()
dormancy_threshold_days = int(LOOKBACK_DAYS)

# A holder is "dormant" when no in/out activity has been seen for this token
# in at least lookback_days days.
sql = f"""
with movements as (
    select "to" as wallet, amount as amt, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select "from" as wallet, -amount as amt, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
),
balances as (
    select wallet, sum(amt) as balance
    from movements
    group by wallet
    having sum(amt) > 0
),
activity as (
    select wallet, min(block_time) as first_tx, max(block_time) as last_tx
    from movements
    group by wallet
)
select
    a.wallet as holder,
    date_diff('day', a.first_tx, now()) as days_since_first,
    date_diff('day', a.last_tx, now()) as days_since_last,
    date_diff('day', a.last_tx, now()) >= {dormancy_threshold_days} as is_dormant
from activity a
join balances b on b.wallet = a.wallet
order by days_since_last desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
