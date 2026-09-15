# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN_ADDRESSES_RAW = '''{{token_addresses}}'''.replace("[", "").replace("]", "").replace('"', "")
DATE_TO = "{{date_to}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(DATE_TO):
    raise ValueError(f"Invalid date_to: {DATE_TO!r}")

token_addresses = [a.strip() for a in TOKEN_ADDRESSES_RAW.split(",") if a.strip()]
if len(token_addresses) < 2:
    raise ValueError("token_addresses must list at least 2 tokens to detect overlap")
for a in token_addresses:
    if not ADDRESS_RE.match(a):
        raise ValueError(f"Invalid token_addresses entry: {a!r}")

token_hex_list = ", ".join(f"from_hex('{a[2:].lower()}')" for a in token_addresses)

sql = f"""
with recipients as (
    select "to" as wallet, contract_address as token, min(block_time) as first_interaction
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address in ({token_hex_list})
      and block_time < date('{DATE_TO}') + interval '1' day
    group by "to", contract_address
)
select
    wallet,
    count(distinct token) as overlapping_tokens,
    date(min(first_interaction)) as first_interaction
from recipients
group by wallet
having count(distinct token) >= 2
order by overlapping_tokens desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
