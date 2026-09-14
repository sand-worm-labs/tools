# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# realized_cap = net held amount (bought - sold) valued at the wallet's own
# average buy price, i.e. what the wallet actually paid for its current bag.
sql = f"""
with buys as (
    select taker as wallet, sum(token_bought_amount) as bought_amt, sum(amount_usd) as bought_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address = from_hex('{token_hex}')
    group by 1
),
sells as (
    select taker as wallet, sum(token_sold_amount) as sold_amt
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_sold_address = from_hex('{token_hex}')
    group by 1
)
select
    '0x' || to_hex(coalesce(b.wallet, s.wallet)) as wallet_address,
    (coalesce(b.bought_amt, 0) - coalesce(s.sold_amt, 0)) * (b.bought_usd / nullif(b.bought_amt, 0)) as realized_cap,
    b.bought_usd / nullif(b.bought_amt, 0) as avg_buy_price
from buys b
full outer join sells s on b.wallet = s.wallet
order by realized_cap desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
