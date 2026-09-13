# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "365"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]
contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with bridge_users as (
    select "from" as wallet, max(nonce) as max_nonce
    from {schema}.transactions
    where "to" = from_hex('{contract_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
tiered as (
    select
        case
            when max_nonce < 10 then '0-9 (new)'
            when max_nonce < 50 then '10-49 (casual)'
            when max_nonce < 200 then '50-199 (active)'
            when max_nonce < 1000 then '200-999 (power user)'
            else '1000+ (veteran)'
        end as nonce_range,
        max_nonce
    from bridge_users
)
select nonce_range, count(*) as wallet_count
from tiered
group by 1
order by min(max_nonce)
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
