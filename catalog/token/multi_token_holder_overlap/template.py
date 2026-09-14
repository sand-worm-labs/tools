# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN1 = "{{token1_address}}".strip()
TOKEN2 = "{{token2_address}}".strip()
TOKEN3 = "{{token3_address}}".strip()
TOKEN4 = "{{token4_address}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN1):
    raise ValueError(f"Invalid token1_address: {TOKEN1!r}")
if not ADDRESS_RE.match(TOKEN2):
    raise ValueError(f"Invalid token2_address: {TOKEN2!r}")
if TOKEN3 and not ADDRESS_RE.match(TOKEN3):
    raise ValueError(f"Invalid token3_address: {TOKEN3!r}")
if TOKEN4 and not ADDRESS_RE.match(TOKEN4):
    raise ValueError(f"Invalid token4_address: {TOKEN4!r}")

tokens = [t[2:].lower() for t in (TOKEN1, TOKEN2, TOKEN3, TOKEN4) if t]

per_token_balances = "\nunion all\n".join(
    f"""
    select contract_address, "to" as holder, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{t}')
    union all
    select contract_address, "from" as holder, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{t}')
    """
    for t in tokens
)

sql = f"""
with movements as (
    {per_token_balances}
),
balances as (
    select contract_address, holder, sum(amt) as balance
    from movements
    group by 1, 2
    having sum(amt) > 0
)
select holder, count(distinct contract_address) as token_count
from balances
group by holder
having count(distinct contract_address) >= 2
order by token_count desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
