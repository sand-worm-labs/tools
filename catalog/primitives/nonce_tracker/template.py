# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET = "{{wallet}}"
DAYS = "{{days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")

# For a non-"all" time range, cumulative_tx_count only counts transactions
# within the selected window, not the wallet's true all-time nonce.
sql = f"""
with daily as (
    select
        date_trunc('day', block_time) as day,
        count(*) as tx_count
    from {CHAIN}.transactions
    where "from" = from_hex('{WALLET[2:].lower()}')
      {{__time_where}}
    group by 1
)
select
    day,
    tx_count,
    sum(tx_count) over (order by day) as cumulative_tx_count
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
