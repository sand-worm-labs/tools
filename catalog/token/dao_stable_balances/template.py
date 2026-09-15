# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DAO_ADDRESSES_RAW = "{{dao_addresses}}".replace("[", "").replace("]", "").replace('"', "")
DATE_TO = "{{date_to}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STABLE_SYMBOLS = ("USDC", "USDT", "DAI", "FRAX", "LUSD", "USDP", "TUSD", "GUSD")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")

dao_addresses = [a.strip() for a in DAO_ADDRESSES_RAW.split(",") if a.strip()]
if not dao_addresses:
    raise ValueError("dao_addresses is required")
for a in dao_addresses:
    if not ADDRESS_RE.match(a):
        raise ValueError(f"Invalid dao_addresses entry: {a!r}")
if DATE_TO and not DATE_RE.match(DATE_TO):
    raise ValueError(f"Invalid date_to: {DATE_TO!r}")

date_where = f"and block_time < date('{DATE_TO}') + interval '1' day" if DATE_TO else ""
dao_in_sql = ", ".join(f"from_hex('{a[2:].lower()}')" for a in dao_addresses)
symbols_in_sql = ", ".join(f"'{s}'" for s in STABLE_SYMBOLS)

# amount_usd on tokens.transfers already accounts for a stablecoin's own price
# feed, so no separate decimals/price join is needed here — summing it nets
# straight to an approximate USD balance (stablecoins trade close to $1).
sql = f"""
with stable_tokens as (
    select contract_address, symbol
    from tokens.erc20
    where blockchain = '{CHAIN}'
      and symbol in ({symbols_in_sql})
),
movements as (
    select t."to" as dao_address, t.contract_address, t.amount_usd as amt
    from tokens.transfers t
    join stable_tokens s on s.contract_address = t.contract_address
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t."to" in ({dao_in_sql})
      {date_where}
    union all
    select t."from" as dao_address, t.contract_address, -t.amount_usd as amt
    from tokens.transfers t
    join stable_tokens s on s.contract_address = t.contract_address
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t."from" in ({dao_in_sql})
      {date_where}
),
balances as (
    select dao_address, contract_address, sum(amt) as usd_balance
    from movements
    group by dao_address, contract_address
    having sum(amt) > 0
)
select
    concat('0x', to_hex(b.dao_address)) as dao_address,
    b.usd_balance,
    s.symbol as token_symbol
from balances b
join stable_tokens s on s.contract_address = b.contract_address
order by b.usd_balance desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
