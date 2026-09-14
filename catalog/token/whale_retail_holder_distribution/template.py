# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
THRESHOLD_USD = "{{threshold_usd}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    threshold_usd_val = float(THRESHOLD_USD) if THRESHOLD_USD else 1000000.0
except ValueError:
    raise ValueError(f"Invalid threshold_usd: {THRESHOLD_USD!r}")
if threshold_usd_val < 0:
    raise ValueError(f"threshold_usd must be >= 0: {THRESHOLD_USD!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

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
    select wallet, sum(amt) as balance_raw
    from movements
    group by wallet
    having sum(amt) > 0
),
-- Latest known price for the token is used to convert every holder's
-- balance to USD; this is a snapshot classification, not historical.
latest_price as (
    select price
    from prices.usd
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{token_hex}')
    order by minute desc
    limit 1
),
priced as (
    select
        b.wallet,
        b.balance_raw / power(10, coalesce(e.decimals, 18)) as balance,
        (b.balance_raw / power(10, coalesce(e.decimals, 18))) * coalesce(lp.price, 0) as balance_usd
    from balances b
    left join tokens.erc20 e
        on e.blockchain = '{CHAIN}' and e.contract_address = from_hex('{token_hex}')
    cross join latest_price lp
),
classified as (
    select
        case when balance_usd >= {threshold_usd_val} then 'whale' else 'retail' end as holder_type,
        balance
    from priced
)
select
    holder_type,
    count(*) as number_of_holders,
    sum(balance) as total_balance,
    100.0 * sum(balance) / nullif(sum(sum(balance)) over (), 0) as percentage
from classified
group by holder_type
order by holder_type
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
