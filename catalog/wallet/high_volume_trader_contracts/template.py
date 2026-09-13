# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}"
LOOKBACK_DAYS = "{{lookback_days}}"
THRESHOLD_USD = "{{threshold_usd}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
try:
    threshold_usd_f = float(THRESHOLD_USD)
except ValueError:
    raise ValueError(f"Invalid threshold_usd: {THRESHOLD_USD!r}")
if threshold_usd_f <= 0:
    raise ValueError(f"Invalid threshold_usd: {THRESHOLD_USD!r}")

sql = f"""
with volume as (
    select t."from" as wallet, sum(t.amount * coalesce(p.price, 0)) as usd_volume
    from tokens.transfers t
    left join prices.usd p on p.blockchain = '{CHAIN}'
        and p.contract_address = t.contract_address
        and p.minute = date_trunc('minute', t.block_time)
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.block_time >= date '{DATE_FROM}'
      and t.block_time < date '{DATE_FROM}' + interval '{LOOKBACK_DAYS}' day
    group by t."from"
),
high_volume as (
    select wallet from volume where usd_volume >= {threshold_usd_f}
),
interactions as (
    select t.contract_address, t."from" as wallet, t.amount * coalesce(p.price, 0) as usd_value
    from tokens.transfers t
    join high_volume h on h.wallet = t."from"
    left join prices.usd p on p.blockchain = '{CHAIN}'
        and p.contract_address = t.contract_address
        and p.minute = date_trunc('minute', t.block_time)
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.block_time >= date '{DATE_FROM}'
      and t.block_time < date '{DATE_FROM}' + interval '{LOOKBACK_DAYS}' day
)
select
    contract_address,
    count(*) as interaction_count,
    count(distinct wallet) as unique_traders,
    sum(usd_value) as total_value_usd
from interactions
group by contract_address
order by interaction_count desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
