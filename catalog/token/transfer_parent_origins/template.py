# Sandworm Power Toolbox — {{__tool_name}}
# No `contract_address` existed on this tool originally; added since a
# per-transfer "parent caller" breakdown needs a specific token to scope to.
# "Parent trace caller" = the immediate on-chain caller of the token
# contract for that transfer's transaction (may differ from tx.from when a
# router/aggregator contract makes the call on the user's behalf).
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
RAW_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if LOOKBACK_DAYS and not (LOOKBACK_DAYS.isdigit() and int(LOOKBACK_DAYS) > 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
raw_schema = RAW_SCHEMA[CHAIN]
lookback_val = int(LOOKBACK_DAYS) if LOOKBACK_DAYS else 30

sql = f"""
with recent_transfers as (
    select block_time, tx_hash, amount
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= now() - interval '{lookback_val}' day
),
origins as (
    select rt.block_time, tr."from" as caller, rt.amount
    from recent_transfers rt
    join {raw_schema}.traces tr
        on tr.tx_hash = rt.tx_hash
        and tr."to" = from_hex('{contract_hex}')
        and tr.call_type = 'call'
        and tr.success = true
)
select
    date_trunc('day', block_time) as time,
    to_hex(caller) as caller,
    count(*) as calls,
    sum(amount) as volume
from origins
group by 1, 2
order by time desc, volume desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
