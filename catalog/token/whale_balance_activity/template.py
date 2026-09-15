# Sandworm Power Toolbox — {{__tool_name}}
# "Solana transfers table" reinterpreted as this catalog's EVM tokens.transfers,
# since this catalog is EVM-only.
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
MIN_BALANCE = "{{min_balance}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    min_balance_val = float(MIN_BALANCE) if MIN_BALANCE else 10000.0
except ValueError:
    raise ValueError(f"Invalid min_balance: {MIN_BALANCE!r}")
if min_balance_val < 0:
    raise ValueError(f"min_balance must be >= 0: {MIN_BALANCE!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with movements as (
    select "to" as wallet, amount as amt_in, 0 as amt_out
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select "from" as wallet, -amount as amt_in, amount as amt_out
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
),
balances as (
    select wallet, sum(amt_in) as balance_raw, sum(amt_out) as out_raw
    from movements
    group by wallet
),
latest_price as (
    select price
    from prices.usd
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{token_hex}')
    order by minute desc
    limit 1
),
priced as (
    select
        b.wallet,
        b.balance_raw / power(10, coalesce(e.decimals, 18)) as final_balance,
        (b.balance_raw / power(10, coalesce(e.decimals, 18))) * coalesce(lp.price, 0) as final_balance_usd,
        (b.out_raw / power(10, coalesce(e.decimals, 18))) * coalesce(lp.price, 0) as volume_out
    from balances b
    left join tokens.erc20 e
        on e.blockchain = '{CHAIN}' and e.contract_address = from_hex('{token_hex}')
    left join latest_price lp on true
)
select
    to_hex(wallet) as wallet,
    final_balance,
    volume_out,
    final_balance_usd / nullif(volume_out, 0) as holder_score
from priced
where final_balance_usd >= {min_balance_val}
order by final_balance_usd desc
limit 200
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
