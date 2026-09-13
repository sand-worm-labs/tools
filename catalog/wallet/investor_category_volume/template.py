# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}"
MIN_USD = "{{min_usd}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if not MIN_USD:
    MIN_USD = "1000"
try:
    min_usd_f = float(MIN_USD)
except ValueError:
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")
if min_usd_f < 0:
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")

sql = f"""
with tx_usd as (
    select t.amount * coalesce(p.price, 0) as usd_value
    from tokens.transfers t
    left join prices.usd p on p.blockchain = '{CHAIN}'
        and p.contract_address = t.contract_address
        and p.minute = date_trunc('minute', t.block_time)
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.block_time >= date '{DATE_FROM}'
),
categorized as (
    select
        case
            when usd_value >= 1000000 then 'whale'
            when usd_value >= 100000 then 'large'
            when usd_value >= 10000 then 'medium'
            else 'small'
        end as category
    from tx_usd
    where usd_value >= {min_usd_f}
)
select category, count(*) as tx_count
from categorized
group by category
order by tx_count desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
