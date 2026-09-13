# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET_ADDRESS = "{{wallet_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "7"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]
wallet_hex = WALLET_ADDRESS[2:].lower()

# current_balance_native is the net native-token change within the lookback
# window, not the wallet's true balance (which needs full history).
sql = f"""
with recent as (
    select block_time, value, "to" as recipient
    from {schema}.transactions
    where ("from" = from_hex('{wallet_hex}') or "to" = from_hex('{wallet_hex}'))
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
)
select
    count(*) as total_transactions,
    min(date(block_time)) as first_activity,
    max(date(block_time)) as last_activity,
    sum(case when recipient = from_hex('{wallet_hex}') then value else -value end) / 1e18 as current_balance_native
from recent
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
