# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
INTERVAL = "{{interval}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

# Price is derived from the token's own trades (amount_usd per unit bought),
# so only trades where this token is the bought leg are used — using both
# legs would double count the same trade at two different implied prices.
sql = f"""
with trades as (
    select
        date_trunc('{INTERVAL}', block_time) as bucket,
        block_time,
        amount_usd / nullif(token_bought_amount, 0) as price
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address = from_hex('{contract_hex}')
      and token_bought_amount > 0
      and amount_usd > 0
),
ranked as (
    select
        bucket,
        price,
        row_number() over (partition by bucket order by block_time asc) as rn_asc,
        row_number() over (partition by bucket order by block_time desc) as rn_desc
    from trades
)
select
    bucket as date,
    max(case when rn_asc = 1 then price end) as open,
    max(price) as high,
    min(price) as low,
    max(case when rn_desc = 1 then price end) as close
from ranked
group by bucket
order by bucket
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
