# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
THRESHOLD_DAYS = "{{threshold_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not THRESHOLD_DAYS.isdigit() or int(THRESHOLD_DAYS) <= 0:
    raise ValueError(f"Invalid threshold_days: {THRESHOLD_DAYS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
threshold_days_val = int(THRESHOLD_DAYS)

# "Retained" = still holding a positive balance and has held since first_trade
# for at least threshold_days; a wallet that sold out entirely is never
# retained regardless of how long it originally held.
sql = f"""
with movements as (
    select "to" as wallet, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select "from" as wallet, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
),
balances as (
    select wallet, sum(amt) as balance
    from movements
    group by wallet
),
first_trade as (
    select "to" as wallet, min(block_time) as first_trade
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    group by "to"
)
select
    f.wallet,
    date(f.first_trade) as first_trade,
    (b.balance > 0 and date_diff('day', f.first_trade, now()) >= {threshold_days_val}) as retained,
    date_diff('day', f.first_trade, now()) as hold_days
from first_trade f
join balances b on b.wallet = f.wallet
order by hold_days desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
