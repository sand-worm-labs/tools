# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
DAYS_BACK = "{{days_back}}".strip()
MIN_VOLUME_USD = "{{min_volume_usd}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DAYS_BACK.isdigit() or int(DAYS_BACK) <= 0:
    raise ValueError(f"Invalid days_back: {DAYS_BACK!r}")
if not MIN_VOLUME_USD.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid min_volume_usd: {MIN_VOLUME_USD!r}")

# Market cap has no direct spellbook table; it is estimated here as
# (latest price) * (circulating supply inferred from net mint/burn transfers),
# restricted to tokens that already cleared the recent-volume floor.
sql = f"""
with recent_trades as (
    select token_bought_address as token_address, sum(amount_usd) as total_volume_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{DAYS_BACK}' day
      and amount_usd is not null
    group by 1
    having sum(amount_usd) >= {MIN_VOLUME_USD}
),
supply as (
    select
        contract_address,
        sum(case when "from" = 0x0000000000000000000000000000000000000000 then amount else 0 end)
        - sum(case when "to" = 0x0000000000000000000000000000000000000000 then amount else 0 end) as circulating_supply
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address in (select token_address from recent_trades)
    group by 1
),
latest_price as (
    select contract_address, price,
        row_number() over (partition by contract_address order by minute desc) as rn
    from prices.usd
    where blockchain = '{CHAIN}'
      and contract_address in (select token_address from recent_trades)
)
select
    r.token_address,
    r.total_volume_usd,
    coalesce(s.circulating_supply, 0) * coalesce(p.price, 0) as est_market_cap
from recent_trades r
left join supply s on s.contract_address = r.token_address
left join latest_price p on p.contract_address = r.token_address and p.rn = 1
order by r.total_volume_usd asc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
