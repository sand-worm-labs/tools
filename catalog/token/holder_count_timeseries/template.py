# Sandworm Power Toolbox — {{__tool_name}}
import json
import re

CONTRACT_ADDRESS = "{{contract_address}}"
DATE_RANGE = json.loads("""{{date_range}}""")
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

FROM_DATE, TO_DATE = str(DATE_RANGE.get("from", "")), str(DATE_RANGE.get("to", ""))
for label, value in (("date_range.from", FROM_DATE), ("date_range.to", TO_DATE)):
    if not DATE_RE.match(value):
        raise ValueError(f"Invalid {label}: {value!r}")
if FROM_DATE > TO_DATE:
    raise ValueError("date_range 'from' must not be after 'to'")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with movements as (
    select date_trunc('day', block_time) as day, "to" as wallet, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and block_time < date('{TO_DATE}') + interval '1' day
    union all
    select date_trunc('day', block_time) as day, "from" as wallet, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and block_time < date('{TO_DATE}') + interval '1' day
),
daily_net as (
    select day, wallet, sum(amt) as net_change
    from movements
    group by day, wallet
),
day_spine as (
    select day from unnest(sequence(date('{FROM_DATE}'), date('{TO_DATE}'), interval '1' day)) as t(day)
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
select day, count(distinct wallet) filter (where balance > 0) as holder_count
from running
group by day
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
