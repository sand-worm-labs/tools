# Sandworm Power Toolbox — {{__tool_name}}
# EVM generalization: pump.fun is Solana-only; "creation" here = a new token's
# mint transfer (from the zero address) inside a transaction sent to
# factory_address, and "dev" = that transaction's sender.
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
    select t.contract_address as token, date_trunc('day', t.block_time) as block_date, tx."from" as dev
    from tokens.transfers t
    join {schema}.transactions tx on tx.hash = t.tx_hash
    where t.blockchain = '{CHAIN}'
      and t."from" = from_hex('{ZERO_ADDRESS_HEX}')
      and tx."to" = from_hex('{factory_hex}')
      and tx.success = true
      and t.block_time between date '{DATE_FROM}' and date '{DATE_TO}' + interval '1' day
),
daily as (
    select block_date, count(distinct token) as token_cnt, count(distinct dev) as dev_cnt
    from creation
    group by 1
)
select
    block_date,
    token_cnt,
    dev_cnt,
    avg(dev_cnt) over (order by block_date rows between 29 preceding and current row) as dev_moving_avg
from daily
order by block_date
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
