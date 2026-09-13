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

# Assumes Dune Spellbook's labels.addresses table with category = 'cex' for
# known centralised-exchange hot wallets.
sql = f"""
with cex_wallets as (
    select address, name
    from labels.addresses
    where blockchain = '{CHAIN}'
      and category = 'cex'
),
matched as (
    select
        t.block_time,
        t.contract_address,
        t.amount,
        case when t."from" = from_hex('{wallet_hex}') then 'deposit_to_cex' else 'withdrawal_from_cex' end as direction,
        c.name as cex_name
    from tokens.transfers t
    join cex_wallets c
      on (t."from" = from_hex('{wallet_hex}') and t."to" = c.address)
      or (t."to" = from_hex('{wallet_hex}') and t."from" = c.address)
    where t.blockchain = '{CHAIN}'
      and t.block_time >= now() - interval '{DAYS}' day
)
select
    date_trunc('day', m.block_time) as day,
    m.direction,
    m.cex_name,
    e.symbol as token_symbol,
    sum((m.amount / power(10, coalesce(e.decimals, 18))) * coalesce(p.price, 0)) as amount_usd,
    count(*) as transfer_count
from matched m
left join tokens.erc20 e on e.blockchain = '{CHAIN}' and e.contract_address = m.contract_address
left join prices.usd p on p.blockchain = '{CHAIN}'
    and p.contract_address = m.contract_address
    and p.minute = date_trunc('minute', m.block_time)
group by 1, 2, 3, 4
order by 1 desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
