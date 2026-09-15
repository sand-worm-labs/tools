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
lookback_days_val = int(LOOKBACK_DAYS)

# Plain daily count of wallets with a net positive running balance over a
# fixed trailing window — the bare-bones member of this tool family (no
# growth-rate columns, no open-ended start, no daily_change/cumulative pair).
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
daily_net as (
    select day, wallet, sum(amt) as net_change
    from movements
    group by day, wallet
),
day_spine as (
    select day from unnest(sequence(current_date - interval '{lookback_days_val}' day, current_date, interval '1' day)) as t(day)
),
wallets as (
    select distinct wallet from movements
),
grid as (
    select s.day, w.wallet, coalesce(m.net_change, 0) as net_change
    from day_spine s
    cross join wallets w
    left join daily_net m on m.day = s.day and m.wallet = w.wallet
),
running as (
    select day, wallet, sum(net_change) over (partition by wallet order by day) as balance
    from grid
)
select day, count(distinct wallet) filter (where balance > 0) as holders
from running
group by day
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
