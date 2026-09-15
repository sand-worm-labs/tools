# Sandworm Power Toolbox — {{__tool_name}}
# "ASC-20" (a Bitcoin/Avalanche inscription standard) generalized to a
# chain-agnostic ERC20 holder ranking, since this catalog is EVM-only.
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
TOTAL_SUPPLY = "{{total_supply}}".strip()
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    total_supply_val = float(TOTAL_SUPPLY) if TOTAL_SUPPLY else 0.0
except ValueError:
    raise ValueError(f"Invalid total_supply: {TOTAL_SUPPLY!r}")
if LIMIT and (not LIMIT.isdigit() or int(LIMIT) <= 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

limit_val = int(LIMIT) if LIMIT else 100
contract_hex = CONTRACT_ADDRESS[2:].lower()
pct_expr = f"total_tokens / {total_supply_val} * 100" if total_supply_val > 0 else "cast(null as double)"

sql = f"""
with movements as (
    select "to" as wallet, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
    union all
    select "from" as wallet, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
),
balances as (
    select wallet, sum(amt) as total_tokens, count(*) as transfer_count
    from movements
    group by wallet
    having sum(amt) > 0
)
select
    rank() over (order by total_tokens desc) as rank,
    '0x' || to_hex(wallet) as wallet_address,
    transfer_count,
    total_tokens,
    {pct_expr} as pct_of_supply
from balances
order by total_tokens desc
limit {limit_val}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
