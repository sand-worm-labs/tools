# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET = "{{wallet}}"
HOPS = "{{hops}}"
MIN_ETH = "{{min_eth}}"
DAYS = "{{days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_HOPS = {"1", "2", "3", "5"}
ALLOWED_MIN_ETH = {"0", "0.01", "0.1", "1"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")
if HOPS not in ALLOWED_HOPS:
    raise ValueError(f"Unsupported hops: {HOPS!r}")
if MIN_ETH not in ALLOWED_MIN_ETH:
    raise ValueError(f"Unsupported min_eth: {MIN_ETH!r}")
if not DAYS.isdigit() or int(DAYS) <= 0:
    raise ValueError(f"Invalid days: {DAYS!r}")

wallet_hex = WALLET[2:].lower()
hops_n = int(HOPS)


# Only ERC20 legs are modeled here — there is no verified chain-generic native
# transfer table, so min_eth filters the (already decimal-normalized) token
# amount from tokens.transfers rather than a strict ETH/USD value.
def _hop_cte(alias, from_filter):
    return f"""{alias} as (
        select "from" as from_address, "to" as to_address, contract_address, amount, block_time
        from tokens.transfers
        where blockchain = '{CHAIN}'
          and token_standard = 'erc20'
          and block_time >= now() - interval '{DAYS}' day
          and amount >= {MIN_ETH}
          and {from_filter}
    )"""


ctes = [_hop_cte("hop_1", f"\"from\" = from_hex('{wallet_hex}')")]
for k in range(2, hops_n + 1):
    ctes.append(_hop_cte(f"hop_{k}", f'"from" in (select to_address from hop_{k - 1})'))

union_sql = " union all ".join(
    f"select {k} as hop, from_address, to_address, contract_address, amount, block_time from hop_{k}"
    for k in range(1, hops_n + 1)
)

sql = f"""
with {','.join(ctes)}
select hop, from_address, to_address, contract_address, amount, block_time
from ({union_sql}) x
order by hop, block_time
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
