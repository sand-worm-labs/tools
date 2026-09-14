# Sandworm Power Toolbox — {{__tool_name}}
import re

TICK = "{{tick}}"
CHAIN = "{{chain}}"
AMT = "{{amt}}"
MIN_DATE = "{{min_date}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
# Dune's raw-transactions schema names BNB Chain "bnb", not "bsc".
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
TICK_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TICK_RE.match(TICK):
    raise ValueError(f"Invalid tick: {TICK!r}")
if not AMT.isdigit() or int(AMT) <= 0:
    raise ValueError(f"Invalid amt: {AMT!r}")
if MIN_DATE and not DATE_RE.match(MIN_DATE):
    raise ValueError(f"Invalid min_date: {MIN_DATE!r}")

schema = CHAIN_SCHEMA[CHAIN]
date_where = f"and block_time >= date('{MIN_DATE}')" if MIN_DATE else ""

# "BSC-20" is not an EVM-wide standard — generalized here to the broader
# ethscriptions-style pattern (a plaintext `data:,{"p":...}` JSON payload
# carried directly as EOA-to-self calldata, no contract involved), which
# BSC-20/PRC-20-style inscriptions on any EVM chain are themselves built on.
sql = f"""
with mints as (
    select "from" as wallet
    from {schema}.transactions
    where success = true
      and from_utf8(data) like '%"p"%'
      and from_utf8(data) like '%"op":"mint"%'
      and from_utf8(data) like '%"tick":"{TICK}"%'
      and from_utf8(data) like '%"amt":"{AMT}"%'
      {date_where}
)
select
    row_number() over (order by count(*) desc) as rank,
    concat('0x', to_hex(wallet)) as wallet,
    count(*) as inscriptions,
    count(*) * {AMT} as total_amount
from mints
group by wallet
order by inscriptions desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
