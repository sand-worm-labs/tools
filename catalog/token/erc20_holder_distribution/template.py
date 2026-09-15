# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
THRESHOLD = "{{threshold}}".strip() or "0"
DECIMALS = "{{decimals}}".strip() or "18"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    threshold_val = float(THRESHOLD)
except ValueError:
    raise ValueError(f"Invalid threshold: {THRESHOLD!r}")
if not DECIMALS.isdigit():
    raise ValueError(f"Invalid decimals: {DECIMALS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with movements as (
    select "to" as wallet, cast(amount_raw as double) as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select "from" as wallet, -cast(amount_raw as double) as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
),
balances as (
    select wallet, sum(amt) / power(10, {DECIMALS}) as balance
    from movements
    group by wallet
    having sum(amt) > 0
)
select
    concat('0x', to_hex(b.wallet)) as address,
    coalesce(l.name, 'Unlabeled') as labels,
    b.balance
from balances b
left join labels.addresses l on l.address = b.wallet and l.blockchain = '{CHAIN}'
where b.balance >= {threshold_val}
order by b.balance desc
limit 1000
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
