# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# Distinct from daily_holder_count (balance-snapshot holders): this counts
# wallets actively transacting the token that day, i.e. daily active holders.
sql = f"""
with activity as (
    select date_trunc('day', block_time) as day, "from" as address
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{token_hex}')
    union
    select date_trunc('day', block_time) as day, "to" as address
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{token_hex}')
),
daily as (
    select day, count(distinct address) as unique_wallets
    from activity
    group by day
)
select day, unique_wallets, unique_wallets - lag(unique_wallets) over (order by day) as daily_change
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
