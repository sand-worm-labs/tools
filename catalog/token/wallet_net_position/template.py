# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
DATE_FROM = "{{date_from}}"
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with buys as (
    select "to" as wallet, sum(amount) as token_bought
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and block_time >= date('{DATE_FROM}')
    group by 1
),
sells as (
    select "from" as wallet, sum(amount) as token_sold
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and block_time >= date('{DATE_FROM}')
    group by 1
)
select
    '0x' || to_hex(coalesce(b.wallet, s.wallet)) as wallet,
    coalesce(b.token_bought, 0) as token_bought,
    coalesce(s.token_sold, 0) as token_sold,
    coalesce(b.token_bought, 0) - coalesce(s.token_sold, 0) as net_position
from buys b
full outer join sells s on b.wallet = s.wallet
order by net_position desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
