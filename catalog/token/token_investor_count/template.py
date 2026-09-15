# Sandworm Power Toolbox — {{__tool_name}}
# No dedicated ERC-3643/T-REX identity-registry table is available in the
# verified Spellbook schemas, so "investors" is derived the same way as any
# ERC20 holder set: distinct addresses currently holding a non-zero balance,
# via standard Transfer events (compliant T-REX tokens still emit these).
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
)
select
    '{CONTRACT_ADDRESS}' as token_address,
    count(*) as investor_count
from balances
where balance > 0
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
