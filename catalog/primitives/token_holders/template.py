# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN_ADDRESS = "{{token_address}}"
TOP_N = "{{top_n}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_TOP_N = {"10", "25", "50", "100"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN_ADDRESS):
    raise ValueError(f"Invalid token_address: {TOKEN_ADDRESS!r}")
if TOP_N not in ALLOWED_TOP_N:
    raise ValueError(f"Unsupported top_n: {TOP_N!r}")

token_hex = TOKEN_ADDRESS[2:].lower()

# Derives balances by netting all historical transfers (in - out) rather than
# reading a balances snapshot table, so it reflects full-history holders only.
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
total as (
    select sum(balance) as total_supply from balances
)
select
    b.wallet,
    b.balance,
    b.balance / t.total_supply * 100 as pct_of_supply
from balances b
cross join total t
order by b.balance desc
limit {TOP_N}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
