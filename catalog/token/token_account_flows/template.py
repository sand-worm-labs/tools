# Sandworm Power Toolbox — {{__tool_name}}
# "Token account" / "mint" (Solana jargon) reinterpreted as an EVM wallet
# address and an ERC20 contract address, since this catalog is EVM-only.
import re

CHAIN = "{{chain}}"
TOKEN_ACCOUNT = "{{token_account}}"
MINT_ADDRESS = "{{mint_address}}"
INTERVAL = "{{interval}}".strip() or "day"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN_ACCOUNT):
    raise ValueError(f"Invalid token_account: {TOKEN_ACCOUNT!r}")
if not ADDRESS_RE.match(MINT_ADDRESS):
    raise ValueError(f"Invalid mint_address: {MINT_ADDRESS!r}")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")

account_hex = TOKEN_ACCOUNT[2:].lower()
mint_hex = MINT_ADDRESS[2:].lower()

sql = f"""
with flows as (
    select date_trunc('{INTERVAL}', block_time) as block_time, amount as deposit, 0 as withdrawal
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{mint_hex}')
      and "to" = from_hex('{account_hex}')
    union all
    select date_trunc('{INTERVAL}', block_time) as block_time, 0 as deposit, amount as withdrawal
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{mint_hex}')
      and "from" = from_hex('{account_hex}')
)
select
    block_time,
    sum(deposit) as deposits,
    sum(withdrawal) as withdrawals
from flows
group by block_time
order by block_time
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
