# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}"
MIN_VALUE = "{{min_value}}".strip() or "0"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
try:
    min_value = float(MIN_VALUE)
except ValueError:
    raise ValueError(f"Invalid min_value: {MIN_VALUE!r}")
if min_value < 0:
    raise ValueError(f"min_value must be >= 0: {MIN_VALUE!r}")

# No token is specified, so this scans ERC20 transfers network-wide on the
# chain; a "roundtrip" is A -> B followed by B -> A of the same token within
# 24 hours, a common wash-trading / self-funding pattern.
sql = f"""
with priced as (
    select
        t."from" as sender,
        t."to" as receiver,
        t.block_time,
        t.contract_address,
        t.amount * coalesce(p.price, 0) as amount_usd
    from tokens.transfers t
    left join prices.usd p
        on p.blockchain = '{CHAIN}'
        and p.contract_address = t.contract_address
        and p.minute = date_trunc('minute', t.block_time)
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t."from" != t."to"
      and t.block_time >= date('{DATE_FROM}')
),
forward as (
    select sender, receiver, contract_address, block_time, amount_usd
    from priced
    where amount_usd >= {min_value}
),
roundtrips as (
    select
        f.sender as from_forward,
        f.receiver as to_forward,
        f.block_time as forward_time,
        b.block_time as back_time,
        f.amount_usd + b.amount_usd as pair_value
    from forward f
    join priced b
        on b.sender = f.receiver
        and b.receiver = f.sender
        and b.contract_address = f.contract_address
        and b.block_time > f.block_time
        and b.block_time <= f.block_time + interval '24' hour
        and b.amount_usd >= {min_value}
)
select
    from_forward,
    to_forward,
    count(*) as cycle_count,
    sum(pair_value) as total_value
from roundtrips
group by 1, 2
order by total_value desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
