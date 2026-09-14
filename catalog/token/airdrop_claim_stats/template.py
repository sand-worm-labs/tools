# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
EXEC_ACCOUNT = "{{exec_account}}"
DATE_FROM = "{{date_from}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
# exec_account is typed "text" in this tool's schema, but it must still be a
# valid address since it's used as the transfer sender.
if not ADDRESS_RE.match(EXEC_ACCOUNT):
    raise ValueError(f"Invalid exec_account: {EXEC_ACCOUNT!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
exec_hex = EXEC_ACCOUNT[2:].lower()

sql = f"""
with claims as (
    select "to" as claimer, amount
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      and "from" = from_hex('{exec_hex}')
      and block_time >= date '{DATE_FROM}'
),
supply as (
    select total_supply / power(10, coalesce(decimals, 18)) as total_supply
    from tokens.erc20
    where blockchain = '{CHAIN}' and contract_address = from_hex('{contract_hex}')
)
select
    sum(c.amount) as total_claimed,
    count(distinct c.claimer) as unique_claimers,
    100.0 * sum(c.amount) / nullif((select total_supply from supply), 0) as perc_claimed
from claims c
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
