# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN1 = "{{chain1}}"
CHAIN2 = "{{chain2}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN1 not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain1: {CHAIN1!r}")
if CHAIN2 not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain2: {CHAIN2!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# Same contract_address is assumed deployed at that literal address on both
# chains; net balance is summed across the two chains per wallet.
sql = f"""
with movements as (
    select "to" as wallet, amount as amt
    from tokens.transfers
    where blockchain in ('{CHAIN1}', '{CHAIN2}')
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select "from" as wallet, -amount as amt
    from tokens.transfers
    where blockchain in ('{CHAIN1}', '{CHAIN2}')
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
)
select
    '0x' || to_hex(wallet) as wallet,
    sum(amt) as net_balance
from movements
group by wallet
order by net_balance desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
