# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN1 = "{{token1_address}}".strip()
TOKEN2 = "{{token2_address}}".strip()
TOKEN3 = "{{token3_address}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN1):
    raise ValueError(f"Invalid token1_address: {TOKEN1!r}")
if TOKEN2 and not ADDRESS_RE.match(TOKEN2):
    raise ValueError(f"Invalid token2_address: {TOKEN2!r}")
if TOKEN3 and not ADDRESS_RE.match(TOKEN3):
    raise ValueError(f"Invalid token3_address: {TOKEN3!r}")

tokens = [t[2:].lower() for t in (TOKEN1, TOKEN2, TOKEN3) if t]

buyer_selects = [
    f"select distinct taker as trader_id from dex.trades "
    f"where blockchain = '{CHAIN}' and token_bought_address = from_hex('{t}')"
    for t in tokens
]

sql = "\nintersect\n".join(buyer_selects)

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
