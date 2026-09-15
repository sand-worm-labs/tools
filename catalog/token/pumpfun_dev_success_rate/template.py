# Sandworm Power Toolbox — {{__tool_name}}
# EVM generalization: pump.fun is Solana-only; "dev" = the sender of the
# creation tx, "created" = a token mint transfer inside a tx sent to
# factory_address, "graduated" = that token's first-ever dex.trades appearance.
import re

CHAIN = "{{chain}}"
FACTORY_ADDRESS = "{{factory_address}}"
DATE_FROM = "{{date_from}}".strip()
MIN_TOKENS = "{{min_tokens}}".strip()

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
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if not MIN_TOKENS:
    MIN_TOKENS = "1"
if not MIN_TOKENS.isdigit() or int(MIN_TOKENS) <= 0:
    raise ValueError(f"Invalid min_tokens: {MIN_TOKENS!r}")

schema = CHAIN_SCHEMA[CHAIN]
factory_hex = FACTORY_ADDRESS[2:].lower()

sql = f"""
with creation as (
    select t.contract_address as token, tx."from" as dev
    from tokens.transfers t
    join {schema}.transactions tx on tx.hash = t.tx_hash
    where t.blockchain = '{CHAIN}'
      and t."from" = from_hex('{ZERO_ADDRESS_HEX}')
      and tx."to" = from_hex('{factory_hex}')
      and tx.success = true
      and t.block_time >= date '{DATE_FROM}'
),
graduation as (
    select token_bought_address as token, min(date_trunc('day', block_time)) as g_day
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address in (select token from creation)
    group by 1
),
per_dev as (
    select
        c.dev,
        count(distinct c.token) as tokens_created,
        count(distinct g.token) as tokens_graduated
    from creation c
    left join graduation g on g.token = c.token
    group by c.dev
)
select
    dev as dev_address,
    tokens_created,
    tokens_graduated,
    tokens_graduated * 1.0 / nullif(tokens_created, 0) as success_rate
from per_dev
where tokens_created >= {MIN_TOKENS}
order by success_rate desc, tokens_created desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
