# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET_ADDRESS = "{{wallet_address}}"
DATE_FROM = "{{date_from}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

wallet_hex = WALLET_ADDRESS[2:].lower()

sql = f"""
with outbound as (
    select date_trunc('month', block_time) as month, "to" as to_address, amount
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and "from" = from_hex('{wallet_hex}')
      and block_time >= date '{DATE_FROM}'
),
agg as (
    select month, to_address, sum(amount) as token_out, count(*) as tx_count
    from outbound
    group by month, to_address
)
select
    month,
    to_address,
    token_out,
    tx_count,
    rank() over (partition by month order by token_out desc) as rank
from agg
order by month, rank
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
