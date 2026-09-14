# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CLAIM_FROM = "{{claim_from}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CLAIM_FROM):
    raise ValueError(f"Invalid claim_from: {CLAIM_FROM!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

claim_from_hex = CLAIM_FROM[2:].lower()
contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with claims as (
    select amount
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      and "from" = from_hex('{claim_from_hex}')
),
bucketed as (
    select
        case
            when amount < 100 then '0-100'
            when amount < 1000 then '100-1000'
            when amount < 10000 then '1000-10000'
            when amount < 100000 then '10000-100000'
            else '100000+'
        end as bucket,
        amount
    from claims
),
totals as (
    select sum(amount) as grand_total, count(*) as grand_count from claims
)
select
    b.bucket,
    count(*) as count,
    sum(b.amount) as total_amount,
    100.0 * count(*) / nullif(t.grand_count, 0) as percentage
from bucketed b
cross join totals t
group by b.bucket, t.grand_count
order by min(b.amount)
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
