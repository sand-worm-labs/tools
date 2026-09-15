# Sandworm Power Toolbox — {{__tool_name}}
# EVM generalization: pump.fun is Solana-only; "launch" = a token mint transfer
# inside a tx sent to factory_address, "graduation" = that token's first-ever
# dex.trades appearance, consistent with catalog/token/daily_graduations.
import json
import re

CHAIN = "{{chain}}"
FACTORY_ADDRESS = "{{factory_address}}"
DATE_RANGE = json.loads('''{{date_range}}''')

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CHAIN_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}
ZERO_ADDRESS_HEX = "0000000000000000000000000000000000000000"

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(FACTORY_ADDRESS):
    raise ValueError(f"Invalid factory_address: {FACTORY_ADDRESS!r}")

DATE_FROM = DATE_RANGE.get("from", "")
DATE_TO = DATE_RANGE.get("to", "")
if not DATE_RE.match(DATE_FROM) or not DATE_RE.match(DATE_TO):
    raise ValueError(f"Invalid date_range: {DATE_RANGE!r}")

schema = CHAIN_SCHEMA[CHAIN]
factory_hex = FACTORY_ADDRESS[2:].lower()

sql = f"""
with creation as (
    select t.contract_address as token, date_trunc('day', t.block_time) as day
    from tokens.transfers t
    join {schema}.transactions tx on tx.hash = t.tx_hash
    where t.blockchain = '{CHAIN}'
      and t."from" = from_hex('{ZERO_ADDRESS_HEX}')
      and tx."to" = from_hex('{factory_hex}')
      and tx.success = true
      and t.block_time between date '{DATE_FROM}' and date '{DATE_TO}' + interval '1' day
),
creation_daily as (
    select day, count(distinct token) as launches
    from creation
    group by 1
),
graduation as (
    select token_bought_address as token, min(date_trunc('day', block_time)) as day
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address in (select token from creation)
    group by 1
),
graduation_daily as (
    select day, count(*) as graduates
    from graduation
    group by 1
)
select
    coalesce(c.day, g.day) as date,
    coalesce(c.launches, 0) as launches,
    coalesce(g.graduates, 0) as graduates,
    coalesce(g.graduates, 0) * 1.0 / nullif(coalesce(c.launches, 0), 0) as graduation_rate
from creation_daily c
full outer join graduation_daily g on g.day = c.day
order by date
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
