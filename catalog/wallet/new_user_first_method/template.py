# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

# tokens.transfers carries no calldata/method selector, so the token_standard
# of each address's first-ever transfer is used as a coarse interaction-type
# proxy for "first method called".
sql = f"""
with first_tx as (
    select
        "from" as address,
        min_by(token_standard, block_time) as interaction_type,
        min(block_time) as first_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
    group by "from"
)
select interaction_type, count(*) as tx_count
from first_tx
where first_time >= date '{DATE_FROM}'
group by interaction_type
order by tx_count desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
