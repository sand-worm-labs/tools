# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

# tokens.erc20 has no creation timestamp, so a token's first transfer is used
# as a proxy for its creation date.
sql = f"""
with token_meta as (
    select contract_address, symbol, name
    from tokens.erc20
    where blockchain = '{CHAIN}'
),
first_seen as (
    select contract_address, min(block_time) as created_at
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
)
select
    tm.name as token_name,
    tm.symbol as token_symbol,
    count(distinct tm.contract_address) as unique_tokens,
    min(fs.created_at) as first_created,
    max(fs.created_at) as last_created,
    date_diff('day', min(fs.created_at), max(fs.created_at)) as time_span
from token_meta tm
join first_seen fs on fs.contract_address = tm.contract_address
where tm.name is not null and tm.symbol is not null
group by tm.name, tm.symbol
having count(distinct tm.contract_address) > 1
order by unique_tokens desc
limit 200
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
