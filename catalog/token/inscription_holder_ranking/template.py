# Sandworm Power Toolbox — {{__tool_name}}
import re

DATA_FILTER = "{{data_filter}}"
AMT = "{{amt}}"
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
# Dune's raw-transactions schema names BNB Chain "bnb", not "bsc".
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
FILTER_RE = re.compile(r"^[A-Za-z0-9_ .:\"-]{1,64}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not FILTER_RE.match(DATA_FILTER):
    raise ValueError(f"Invalid data_filter: {DATA_FILTER!r}")
if not AMT.isdigit() or int(AMT) <= 0:
    raise ValueError(f"Invalid amt: {AMT!r}")

schema = CHAIN_SCHEMA[CHAIN]

# PRC-20 is a Polygon-branded name for the same ethscriptions-style pattern
# used on every EVM chain: a plaintext `data:,{"p":...}` JSON payload sent as
# EOA calldata with no contract involved. data_filter is a free substring
# match against that payload (e.g. a tick name) rather than a fixed field, so
# this one tool covers any such inscription protocol variant on any chain.
sql = f"""
with mints as (
    select "from" as wallet
    from {schema}.transactions
    where success = true
      and from_utf8(data) like '%"op":"mint"%'
      and from_utf8(data) like '%{DATA_FILTER}%'
      and from_utf8(data) like '%"amt":"{AMT}"%'
)
select
    row_number() over (order by count(*) desc) as rank,
    concat('0x', to_hex(wallet)) as wallet_address,
    count(*) as mint_count,
    count(*) * {AMT} as total_amount
from mints
group by wallet
order by mint_count desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
