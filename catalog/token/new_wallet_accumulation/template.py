# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
scan_days = int(LOOKBACK_DAYS) * 3

# A recipient counts as a "new wallet" if its earliest receipt of this token
# across the wider scan window falls inside the requested lookback window
# (a cheap proxy for "never held before", since scanning tokens.transfers
# unbounded is too costly).
sql = f"""
with transfers as (
    select block_time, "to" as wallet, amount
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= now() - interval '{scan_days}' day
),
first_recv as (
    select wallet, min(block_time) as first_time
    from transfers
    group by 1
    having min(block_time) >= now() - interval '{LOOKBACK_DAYS}' day
)
select
    date_trunc('day', t.block_time) as time,
    count(distinct t.wallet) as new_holders,
    sum(t.amount) as accumulated_amount
from transfers t
join first_recv f on f.wallet = t.wallet and f.first_time = t.block_time
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
