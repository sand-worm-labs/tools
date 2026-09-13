# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET = "{{wallet}}"
DAYS = "{{days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")
if not DAYS.isdigit() or int(DAYS) <= 0:
    raise ValueError(f"Invalid days: {DAYS!r}")

wallet_hex = WALLET[2:].lower()

sql = f"""
with transfers as (
    select
        contract_address,
        case when "to" = from_hex('{wallet_hex}') then 'buy' else 'sell' end as side,
        amount,
        block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and ("to" = from_hex('{wallet_hex}') or "from" = from_hex('{wallet_hex}'))
      and block_time >= now() - interval '{DAYS}' day
),
priced as (
    select
        t.contract_address,
        t.side,
        t.amount,
        t.amount * coalesce(p.price, 0) as usd_value
    from transfers t
    left join prices.usd p on p.blockchain = '{CHAIN}'
        and p.contract_address = t.contract_address
        and p.minute = date_trunc('minute', t.block_time)
),
agg as (
    select
        contract_address,
        sum(case when side = 'buy' then amount else 0 end) as bought_amount,
        sum(case when side = 'buy' then usd_value else 0 end) as bought_usd,
        sum(case when side = 'sell' then amount else 0 end) as sold_amount,
        sum(case when side = 'sell' then usd_value else 0 end) as sold_usd
    from priced
    group by contract_address
)
select
    contract_address,
    bought_amount,
    sold_amount,
    bought_usd,
    sold_usd,
    sold_usd - (sold_amount * (bought_usd / nullif(bought_amount, 0))) as realized_pnl_usd
from agg
where sold_amount > 0
order by realized_pnl_usd desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
