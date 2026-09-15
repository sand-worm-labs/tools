# Sandworm Power Toolbox — {{__tool_name}}
# "SOL amounts" generalized to native-gas-token amounts on the selected EVM chain.
CHAIN = "{{chain}}"
DAYS_BACK = "{{days_back}}".strip()
MIN_IN = "{{min_transfer_in_sum_amount}}".strip()
MIN_OUT = "{{single_transfer_out_min_amount}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
RAW_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}
DISPATCH_SUSPICIOUS_THRESHOLD = 5

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DAYS_BACK.isdigit() or int(DAYS_BACK) <= 0:
    raise ValueError(f"Invalid days_back: {DAYS_BACK!r}")
try:
    min_in_val = float(MIN_IN) if MIN_IN else 50.0
    min_out_val = float(MIN_OUT) if MIN_OUT else 0.1
except ValueError:
    raise ValueError(f"Invalid inflow/outflow threshold: {MIN_IN!r}, {MIN_OUT!r}")
if min_in_val <= 0 or min_out_val <= 0:
    raise ValueError("Thresholds must be > 0")

raw_schema = RAW_SCHEMA[CHAIN]
days_back = int(DAYS_BACK)

sql = f"""
with cex_inflows as (
    select t."to" as wallet, sum(t.value / 1e18) as inflow_native
    from {raw_schema}.traces t
    join labels.addresses l on l.address = t."from" and l.blockchain = '{CHAIN}' and l.category = 'cex'
    where t.call_type = 'call'
      and t.success = true
      and t.value > 0
      and t.block_time >= now() - interval '{days_back}' day
    group by t."to"
    having sum(t.value / 1e18) >= {min_in_val}
),
dispatches as (
    select tr."from" as wallet, count(*) as dispatch_count
    from {raw_schema}.traces tr
    where tr.call_type = 'call'
      and tr.success = true
      and tr.value / 1e18 >= {min_out_val}
      and tr.block_time >= now() - interval '{days_back}' day
      and tr."from" in (select wallet from cex_inflows)
    group by tr."from"
)
select
    '0x' || to_hex(c.wallet) as wallet,
    cast(coalesce(d.dispatch_count, 0) as double) / nullif(c.inflow_native, 0) as dispatch_score,
    coalesce(d.dispatch_count, 0) as dispatch_count,
    coalesce(d.dispatch_count, 0) >= {DISPATCH_SUSPICIOUS_THRESHOLD} as suspicious
from cex_inflows c
left join dispatches d on d.wallet = c.wallet
order by dispatch_score desc nulls last
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
