# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}"
THRESHOLD_USD = "{{threshold_usd}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
try:
    threshold_usd_val = float(THRESHOLD_USD) if THRESHOLD_USD else 500.0
except ValueError:
    raise ValueError(f"Invalid threshold_usd: {THRESHOLD_USD!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with movements as (
    select "to" as wallet, amount as amt, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    union all
    select "from" as wallet, -amount as amt, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
priced as (
    select
        m.wallet,
        (m.amt / power(10, coalesce(e.decimals, 18))) * coalesce(p.price, 0) as amt_usd
    from movements m
    left join tokens.erc20 e
        on e.blockchain = '{CHAIN}' and e.contract_address = from_hex('{token_hex}')
    left join prices.usd p
        on p.blockchain = '{CHAIN}' and p.contract_address = from_hex('{token_hex}')
        and p.minute = date_trunc('minute', m.block_time)
),
per_wallet as (
    select wallet, sum(amt_usd) as net_usd
    from priced
    group by wallet
)
select
    to_hex(wallet) as wallet,
    net_usd,
    net_usd > 0 as is_accumulating
from per_wallet
where net_usd >= {threshold_usd_val}
order by net_usd desc
limit 200
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
