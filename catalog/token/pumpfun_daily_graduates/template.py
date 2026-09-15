# Sandworm Power Toolbox — {{__tool_name}}
# EVM generalization: pump.fun is Solana-only; "creation" = a token mint
# transfer inside a tx sent to factory_address, "graduation" = that token's
# first-ever dex.trades appearance (bonding-curve liquidity migrating to a
# DEX pool), consistent with catalog/token/daily_graduations.
import re

CHAIN = "{{chain}}"
FACTORY_ADDRESS = "{{factory_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
CHAIN_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}
ZERO_ADDRESS_HEX = "0000000000000000000000000000000000000000"

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(FACTORY_ADDRESS):
    raise ValueError(f"Invalid factory_address: {FACTORY_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]
factory_hex = FACTORY_ADDRESS[2:].lower()

sql = f"""
with creation as (
    select t.contract_address as token
    from tokens.transfers t
    join {schema}.transactions tx on tx.hash = t.tx_hash
    where t.blockchain = '{CHAIN}'
      and t."from" = from_hex('{ZERO_ADDRESS_HEX}')
      and tx."to" = from_hex('{factory_hex}')
      and tx.success = true
      and t.block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
graduation as (
    select token_bought_address as token, min(date_trunc('day', block_time)) as day
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address in (select token from creation)
    group by 1
)
select day, count(*) as graduate_count
from graduation
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
