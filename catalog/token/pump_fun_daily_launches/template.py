# Sandworm Power Toolbox — {{__tool_name}}
# EVM generalization: pump.fun is Solana-only; "launch" here = a new token's
# mint transfer (from the zero address) inside a tx sent to factory_address.
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

DATE_FROM = (DATE_RANGE.get("from") or "").strip()
DATE_TO = (DATE_RANGE.get("to") or "").strip()
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_range.from: {DATE_FROM!r}")
if DATE_TO and not DATE_RE.match(DATE_TO):
    raise ValueError(f"Invalid date_range.to: {DATE_TO!r}")

schema = CHAIN_SCHEMA[CHAIN]
factory_hex = FACTORY_ADDRESS[2:].lower()

date_where = ""
if DATE_FROM:
    date_where += f" and t.block_time >= date '{DATE_FROM}'"
if DATE_TO:
    date_where += f" and t.block_time < date '{DATE_TO}' + interval '1' day"

sql = f"""
with creation as (
    select t.contract_address as token, date_trunc('day', t.block_time) as day
    from tokens.transfers t
    join {schema}.transactions tx on tx.hash = t.tx_hash
    where t.blockchain = '{CHAIN}'
      and t."from" = from_hex('{ZERO_ADDRESS_HEX}')
      and tx."to" = from_hex('{factory_hex}')
      and tx.success = true
      {date_where}
),
daily as (
    select day, count(distinct token) as tokens_launched
    from creation
    group by 1
)
select
    day,
    tokens_launched,
    sum(tokens_launched) over (order by day) as cumulative_launches
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
