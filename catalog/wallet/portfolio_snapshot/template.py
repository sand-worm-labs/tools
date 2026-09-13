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

sql = f"""
with movements as (
    select contract_address, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and "to" = from_hex('{wallet_hex}')
    union all
    select contract_address, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and "from" = from_hex('{wallet_hex}')
),
balances as (
    select contract_address, sum(amt) as balance
    from movements
    group by contract_address
    having sum(amt) > 0
),
latest_price as (
    select contract_address, price
    from (
        select contract_address, price, row_number() over (partition by contract_address order by minute desc) as rn
        from prices.usd
        where blockchain = '{CHAIN}'
    ) ranked
    where rn = 1
)
select
    b.contract_address,
    e.symbol as token_symbol,
    b.balance,
    lp.price as price_usd,
    b.balance * coalesce(lp.price, 0) as value_usd
from balances b
left join tokens.erc20 e on e.blockchain = '{CHAIN}' and e.contract_address = b.contract_address
left join latest_price lp on lp.contract_address = b.contract_address
order by value_usd desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
