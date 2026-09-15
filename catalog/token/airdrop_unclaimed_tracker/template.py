# Sandworm Power Toolbox — {{__tool_name}}
# Generalized to any EVM distributor contract: inbound ERC20 transfers fund
# the airdrop pool (total allocation), outbound transfers are claims.
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if LOOKBACK_DAYS and (not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

lookback_days = int(LOOKBACK_DAYS) if LOOKBACK_DAYS else 30
contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with movements as (
    select
        date_trunc('day', t.block_time) as day,
        (t.amount / power(10, coalesce(e.decimals, 18))) * coalesce(p.price, 0) as amount_usd,
        1 as is_inflow
    from tokens.transfers t
    left join tokens.erc20 e on e.blockchain = '{CHAIN}' and e.contract_address = t.contract_address
    left join prices.usd p on p.blockchain = '{CHAIN}'
        and p.contract_address = t.contract_address
        and p.minute = date_trunc('minute', t.block_time)
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t."to" = from_hex('{contract_hex}')
      and t.block_time >= now() - interval '{lookback_days}' day
    union all
    select
        date_trunc('day', t.block_time) as day,
        (t.amount / power(10, coalesce(e.decimals, 18))) * coalesce(p.price, 0) as amount_usd,
        0 as is_inflow
    from tokens.transfers t
    left join tokens.erc20 e on e.blockchain = '{CHAIN}' and e.contract_address = t.contract_address
    left join prices.usd p on p.blockchain = '{CHAIN}'
        and p.contract_address = t.contract_address
        and p.minute = date_trunc('minute', t.block_time)
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t."from" = from_hex('{contract_hex}')
      and t.block_time >= now() - interval '{lookback_days}' day
),
daily as (
    select
        day,
        sum(case when is_inflow = 1 then amount_usd else 0 end) as allocated_usd,
        sum(case when is_inflow = 0 then amount_usd else 0 end) as claimed_usd
    from movements
    group by day
)
select
    cast(day as date) as claim_date,
    sum(allocated_usd) over (order by day) as total_allocated_usd,
    sum(claimed_usd) over (order by day) as claimed_usd,
    sum(allocated_usd) over (order by day) - sum(claimed_usd) over (order by day) as unclaimed_usd
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
