# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET_ADDRESS = "{{wallet_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")

wallet_hex = WALLET_ADDRESS[2:].lower()

sql = f"""
with counterparties as (
    select distinct case when "from" = from_hex('{wallet_hex}') then "to" else "from" end as counterparty
    from {CHAIN}.transactions
    where "from" = from_hex('{wallet_hex}') or "to" = from_hex('{wallet_hex}')
),
degree as (
    select t."to" as counterparty, count(distinct t."from") as in_degree
    from {CHAIN}.transactions t
    join counterparties c on t."to" = c.counterparty
    group by 1
)
select avg(in_degree) as avg_degree
from degree
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
