# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
TOP_N = "{{top_n}}".strip() or "100"
EXCLUDE_TREASURY = "{{exclude_treasury}}".strip().lower() or "true"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not TOP_N.isdigit() or int(TOP_N) <= 0:
    raise ValueError(f"Invalid top_n: {TOP_N!r}")
if EXCLUDE_TREASURY not in {"true", "false"}:
    raise ValueError(f"Invalid exclude_treasury: {EXCLUDE_TREASURY!r}, expected 'true' or 'false'")

token_hex = CONTRACT_ADDRESS[2:].lower()
# No universal "treasury" address exists for an arbitrary ERC20 — the closest
# EVM-generic equivalent is excluding the null address, which is where
# mint/burn flows land and would otherwise skew top-holder balances.
treasury_filter = "and wallet <> from_hex('0000000000000000000000000000000000000000')" if EXCLUDE_TREASURY == "true" else ""

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
    select wallet, sum(amt) as net_balance
    from movements
    group by wallet
    having sum(amt) > 0
)
select
    to_hex(wallet) as address,
    net_balance,
    row_number() over (order by net_balance desc) as rank
from balances
where 1 = 1 {treasury_filter}
order by net_balance desc
limit {TOP_N}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
