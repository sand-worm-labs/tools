# Sandworm Power Toolbox — {{__tool_name}}
import json
import re
from datetime import datetime

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DATE_RANGE = """{{date_range}}"""

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    date_range = json.loads(DATE_RANGE)
    date_from = str(date_range["from"]).strip()
    date_to = str(date_range["to"]).strip()
    datetime.strptime(date_from, "%Y-%m-%d")
    datetime.strptime(date_to, "%Y-%m-%d")
except (json.JSONDecodeError, KeyError, ValueError):
    raise ValueError(f"Invalid date_range: {DATE_RANGE!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with airdrop_recipients as (
    select distinct "to" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= date '{date_from}'
      and block_time < date '{date_to}' + interval '1' day
),
movements as (
    select t."to" as wallet, t.amount as amt
    from tokens.transfers t
    join airdrop_recipients r on r.wallet = t."to"
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{contract_hex}')
    union all
    select t."from" as wallet, -t.amount as amt
    from tokens.transfers t
    join airdrop_recipients r on r.wallet = t."from"
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{contract_hex}')
),
balances as (
    select wallet, sum(amt) as net_balance
    from movements
    group by wallet
)
select
    '0x' || to_hex(wallet) as user,
    net_balance,
    net_balance > 0 as retained
from balances
order by net_balance desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
