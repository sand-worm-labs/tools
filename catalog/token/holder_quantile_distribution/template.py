# Sandworm Power Toolbox — {{__tool_name}}
# g5 originally cited a Solana account-activity table; this catalog is
# EVM-only, so holder balances are derived from ERC20 transfer movements.
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
    select wallet, sum(amt) as balance
    from movements
    group by wallet
    having sum(amt) > 0
),
quantiled as (
    select
        wallet,
        balance,
        ntile(4) over (order by balance) as q
    from balances
)
select
    case q
        when 1 then 'Q1 (smallest 25%)'
        when 2 then 'Q2'
        when 3 then 'Q3'
        when 4 then 'Q4 (largest 25%)'
    end as quantile_bucket,
    count(*) as holder_count,
    sum(balance) as total_held
from quantiled
group by q
order by q
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
