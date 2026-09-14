# Sandworm Power Toolbox — {{__tool_name}}
# "ETH transfers" reinterpreted generically as native-gas-token transfers on
# whichever EVM chain is selected (native value moved via CALL traces), since
# this catalog is EVM-only and chain-agnostic.
from datetime import datetime

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}".strip()
MIN_ETH = "{{min_eth}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
RAW_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
try:
    datetime.strptime(DATE_FROM, "%Y-%m-%d")
except ValueError:
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
try:
    min_eth_val = float(MIN_ETH) if MIN_ETH else 1000.0
except ValueError:
    raise ValueError(f"Invalid min_eth: {MIN_ETH!r}")
if min_eth_val <= 0:
    raise ValueError(f"min_eth must be > 0: {MIN_ETH!r}")

raw_schema = RAW_SCHEMA[CHAIN]
whale_cutoff = min_eth_val * 3
mega_whale_cutoff = min_eth_val * 10

sql = f"""
with native_transfers as (
    select date_trunc('month', block_time) as month, value / 1e18 as amount_native
    from {raw_schema}.traces
    where call_type = 'call'
      and value > 0
      and success = true
      and block_time >= date '{DATE_FROM}'
),
categorized as (
    select
        month,
        amount_native,
        case
            when amount_native >= {mega_whale_cutoff} then 'mega_whale'
            when amount_native >= {whale_cutoff} then 'whale'
            else 'large_holder'
        end as whale_category
    from native_transfers
    where amount_native >= {min_eth_val}
)
select
    month,
    whale_category,
    count(*) as num_transactions,
    sum(amount_native) as eth_transfer
from categorized
group by month, whale_category
order by month desc, eth_transfer desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
