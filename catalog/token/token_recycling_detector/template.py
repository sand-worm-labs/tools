# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
MIN_USD = "{{min_usd}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    min_usd_val = float(MIN_USD) if MIN_USD else 1000.0
except ValueError:
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

# "Recycling" = a wallet receives tokens then forwards ~the same amount
# onward within 24h (funnel/wash pattern); flagged suspicious when the
# reuse gap is under 1 hour.
sql = f"""
with priced_transfers as (
    select
        t.block_time,
        t."from",
        t."to",
        t.amount,
        t.amount * coalesce(p.price, 0) as amount_usd
    from tokens.transfers t
    left join prices.usd p
        on p.blockchain = '{CHAIN}'
        and p.contract_address = t.contract_address
        and p.minute = date_trunc('minute', t.block_time)
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{contract_hex}')
),
inbound as (
    select "to" as wallet, block_time as in_time, amount as in_amount
    from priced_transfers
    where amount_usd >= {min_usd_val}
),
outbound as (
    select "from" as wallet, block_time as out_time, amount as out_amount
    from priced_transfers
),
matched as (
    select
        date_diff('minute', i.in_time, o.out_time) / 60.0 as time_diff_hours
    from inbound i
    join outbound o
        on o.wallet = i.wallet
        and o.out_time > i.in_time
        and o.out_time <= i.in_time + interval '24' hour
        and abs(o.out_amount - i.in_amount) <= i.in_amount * 0.05
)
select
    round(time_diff_hours, 1) as time_diff_hours,
    count(*) as reuse_count,
    (time_diff_hours < 1) as suspicious_transfers
from matched
group by 1, 3
order by time_diff_hours
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
