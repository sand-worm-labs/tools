# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
date_where = f"and block_time >= date('{DATE_FROM}')" if DATE_FROM else ""

sql = f"""
with trades as (
    select
        taker as wallet,
        case when token_bought_address = from_hex('{contract_hex}') then token_bought_amount_usd else 0 end as buy_usd,
        case when token_sold_address = from_hex('{contract_hex}') then token_sold_amount_usd else 0 end as sell_usd,
        case when token_bought_address = from_hex('{contract_hex}') then token_bought_amount else 0 end as bought_amount,
        case when token_sold_address = from_hex('{contract_hex}') then token_sold_amount else 0 end as sold_amount
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{contract_hex}') or token_sold_address = from_hex('{contract_hex}'))
      {date_where}
)
select
    to_hex(wallet) as wallet,
    sum(buy_usd) as buy_usd,
    sum(sell_usd) as sell_usd,
    sum(sell_usd) - sum(buy_usd) as net_pnl,
    sum(bought_amount) - sum(sold_amount) as token_held
from trades
group by wallet
order by net_pnl desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
