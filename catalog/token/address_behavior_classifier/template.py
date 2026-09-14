# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "365"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with movements as (
    select "from" as address, block_time, amount_usd, "to" as counterparty
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    union all
    select "to" as address, block_time, amount_usd, "from" as counterparty
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
stats as (
    select
        address,
        count(*) as tx_count,
        sum(amount_usd) as volume,
        count(distinct date_trunc('day', block_time)) as active_days,
        count(distinct counterparty) as unique_counterparties
    from movements
    group by address
)
select
    to_hex(address) as address,
    case
        when unique_counterparties > 500 and tx_count > 1000 then 'cex'
        when tx_count > 200 and active_days > {LOOKBACK_DAYS} * 0.5 then 'market_maker'
        when volume > 1000000 and tx_count < 50 then 'whale'
        else 'retail'
    end as classification,
    tx_count,
    volume,
    active_days
from stats
order by volume desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
