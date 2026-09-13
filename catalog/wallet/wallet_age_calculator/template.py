# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET_ADDRESS = "{{wallet_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")

schema = CHAIN_SCHEMA[CHAIN]
wallet_hex = WALLET_ADDRESS[2:].lower()

sql = f"""
with bounds as (
    select min(block_time) as first_block_time, max(block_time) as last_block_time
    from {schema}.transactions
    where "from" = from_hex('{wallet_hex}')
)
select
    '{WALLET_ADDRESS}' as wallet_address,
    date(first_block_time) as first_transaction_date,
    date_diff('day', first_block_time, now()) as wallet_age_days,
    date_diff('day', last_block_time, now()) as inactive_since_in_days
from bounds
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
