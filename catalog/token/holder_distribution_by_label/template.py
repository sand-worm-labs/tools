# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
TOP_N = "{{top_n}}".strip() or "200"
DECIMALS = "{{decimals}}"
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not TOP_N.isdigit() or int(TOP_N) <= 0:
    raise ValueError(f"Invalid top_n: {TOP_N!r}")
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
),
top_holders as (
    select wallet, balance
    from balances
    order by balance desc
    limit {TOP_N}
),
labeled as (
    select
        coalesce(l.name, 'Unlabeled') as label,
        t.balance
    from top_holders t
    left join labels.addresses l on l.address = t.wallet and l.blockchain = '{CHAIN}'
)
select
    label,
    sum(balance) as balance,
    100.0 * sum(balance) / sum(sum(balance)) over () as pct
from labeled
group by label
order by balance desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
