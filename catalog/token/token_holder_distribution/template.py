# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
zero_hex = "0" * 40

sql = f"""
with movements as (
    select "to" as address, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "to" <> from_hex('{zero_hex}')
    union all
    select "from" as address, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "from" <> from_hex('{zero_hex}')
),
balances as (
    select address, sum(amt) as balance
    from movements
    group by address
    having sum(amt) > 0
),
total as (
    select sum(balance) as total_supply from balances
),
tiered as (
    select
        b.balance,
        case
            when b.balance / t.total_supply >= 0.01 then 'whale (>=1%)'
            when b.balance / t.total_supply >= 0.001 then 'large (0.1-1%)'
            when b.balance / t.total_supply >= 0.0001 then 'medium (0.01-0.1%)'
            else 'small (<0.01%)'
        end as bucket
    from balances b
    cross join total t
)
select
    bucket,
    count(*) as holder_count,
    sum(balance) / (select total_supply from total) as total_supply_pct
from tiered
group by bucket
order by total_supply_pct desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
