# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET = "{{wallet}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")

schema = CHAIN_SCHEMA[CHAIN]
wallet_hex = WALLET[2:].lower()

sql = f"""
with first_tx as (
    select block_time, "to" as counterparty
    from {schema}.transactions
    where "from" = from_hex('{wallet_hex}')
    order by block_time asc
    limit 1
)
select
    date(block_time) as first_tx_date,
    date_diff('day', block_time, now()) as wallet_age_days,
    to_hex(counterparty) as first_counterparty
from first_tx
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
