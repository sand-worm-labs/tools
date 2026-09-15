# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN_A = "{{token_a}}"
TOKEN_B = "{{token_b}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN_A):
    raise ValueError(f"Invalid token_a: {TOKEN_A!r}")
if not ADDRESS_RE.match(TOKEN_B):
    raise ValueError(f"Invalid token_b: {TOKEN_B!r}")
if TOKEN_A.lower() == TOKEN_B.lower():
    raise ValueError("token_a and token_b must differ")

token_a_hex = TOKEN_A[2:].lower()
token_b_hex = TOKEN_B[2:].lower()

# Peg ratio = A per B, pooled from both trade directions so days with only
# one-sided flow still get a ratio.
sql = f"""
with directional as (
    select block_time, token_bought_amount as amt_a, token_sold_amount as amt_b
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address = from_hex('{token_a_hex}')
      and token_sold_address = from_hex('{token_b_hex}')
    union all
    select block_time, token_sold_amount as amt_a, token_bought_amount as amt_b
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_sold_address = from_hex('{token_a_hex}')
      and token_bought_address = from_hex('{token_b_hex}')
)
select
    date_trunc('day', block_time) as day,
    sum(amt_a) / nullif(sum(amt_b), 0) as steth_eth_ratio
from directional
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
