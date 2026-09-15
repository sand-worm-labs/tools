# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}"
TOP_N = "{{top_n}}".strip()
MIN_USD = "{{min_usd}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if TOP_N and not (TOP_N.isdigit() and int(TOP_N) > 0):
    raise ValueError(f"Invalid top_n: {TOP_N!r}")
try:
    min_usd_val = float(MIN_USD) if MIN_USD else 1000.0
except ValueError:
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
top_n_val = int(TOP_N) if TOP_N else 1000

sql = f"""
with current_bal as (
    select address, sum(amt) as balance
    from (
        select "to" as address, amount as amt from tokens.transfers
        where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{contract_hex}')
        union all
        select "from" as address, -amount as amt from tokens.transfers
        where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{contract_hex}')
    ) m
    group by address
),
previous_bal as (
    select address, sum(amt) as balance
    from (
        select "to" as address, amount as amt from tokens.transfers
        where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{contract_hex}')
          and block_time < date('{DATE_FROM}')
        union all
        select "from" as address, -amount as amt from tokens.transfers
        where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{contract_hex}')
          and block_time < date('{DATE_FROM}')
    ) m
    group by address
),
joined as (
    select
        coalesce(c.address, p.address) as address,
        coalesce(c.balance, 0) as current_hold,
        coalesce(p.balance, 0) as previous_hold
    from current_bal c
    full outer join previous_bal p on p.address = c.address
),
latest_price as (
    select price
    from prices.usd
    where blockchain = '{CHAIN}' and contract_address = from_hex('{contract_hex}')
    order by minute desc
    limit 1
)
select
    to_hex(j.address) as holder_address,
    j.current_hold,
    j.previous_hold,
    (j.current_hold - j.previous_hold) / nullif(abs(j.previous_hold), 0) * 100 as pct_change
from joined j
cross join latest_price lp
where j.current_hold * coalesce(lp.price, 0) >= {min_usd_val}
order by j.current_hold desc
limit {top_n_val}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
