# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET = "{{wallet}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")

wallet_hex = WALLET[2:].lower()

# Average-cost-basis method: cost basis per unit is the volume-weighted
# average USD price paid across all inbound transfers ever seen for the
# wallet, applied uniformly to both sold and still-held units.
sql = f"""
with transfers as (
    select
        contract_address as token_address,
        block_time,
        case when "to" = from_hex('{wallet_hex}') then amount else -amount end as signed_amount,
        case when "to" = from_hex('{wallet_hex}') then 1 else 0 end as is_buy
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and ("to" = from_hex('{wallet_hex}') or "from" = from_hex('{wallet_hex}'))
),
priced as (
    select
        t.token_address,
        t.signed_amount,
        t.is_buy,
        p.price
    from transfers t
    left join prices.usd p
        on p.blockchain = '{CHAIN}'
       and p.contract_address = t.token_address
       and p.minute = date_trunc('minute', t.block_time)
),
agg as (
    select
        token_address,
        sum(signed_amount) as net_balance,
        sum(case when is_buy = 1 then signed_amount else 0 end) as total_bought,
        sum(case when is_buy = 1 then signed_amount * price else 0 end) as total_cost_usd,
        sum(case when is_buy = 0 then -signed_amount else 0 end) as total_sold,
        sum(case when is_buy = 0 then -signed_amount * price else 0 end) as total_proceeds_usd
    from priced
    group by token_address
),
latest_price as (
    select contract_address as token_address, price
    from (
        select
            contract_address,
            price,
            row_number() over (partition by contract_address order by minute desc) as rn
        from prices.usd
        where blockchain = '{CHAIN}'
          and contract_address in (select token_address from agg)
    ) ranked
    where rn = 1
)
select
    to_hex(a.token_address) as token_address,
    a.net_balance,
    coalesce(a.total_cost_usd, 0) / nullif(a.total_bought, 0) as avg_cost_basis,
    coalesce(a.total_proceeds_usd, 0)
        - (coalesce(a.total_sold, 0) * (coalesce(a.total_cost_usd, 0) / nullif(a.total_bought, 0))) as realized_gain_usd,
    (a.net_balance * lp.price)
        - (a.net_balance * (coalesce(a.total_cost_usd, 0) / nullif(a.total_bought, 0))) as unrealized_gain_usd,
    lp.price as current_price_usd
from agg a
left join latest_price lp on lp.token_address = a.token_address
order by unrealized_gain_usd desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
