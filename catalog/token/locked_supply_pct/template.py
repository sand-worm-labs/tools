# Sandworm Power Toolbox — {{__tool_name}}
# Generalized from a PLS-specific supply query to any EVM ERC20 token + vault
# address pair: circulating_supply = net mints minus burns, locked_supply = the
# vault's net inbound balance, both measured over the lookback window.
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOCKER_ADDRESS = "{{locker_address}}"
LOOKBACK_DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
ZERO_HEX = "0000000000000000000000000000000000000000"

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not ADDRESS_RE.match(LOCKER_ADDRESS):
    raise ValueError(f"Invalid locker_address: {LOCKER_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
locker_hex = LOCKER_ADDRESS[2:].lower()

sql = f"""
with transfers as (
    select "from", "to", amount
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
mint_burn as (
    select
        sum(case when "from" = from_hex('{ZERO_HEX}') then amount else 0 end) as minted,
        sum(case when "to" = from_hex('{ZERO_HEX}') then amount else 0 end) as burned
    from transfers
),
locker_balance as (
    select
        sum(case when "to" = from_hex('{locker_hex}') then amount else 0 end)
        - sum(case when "from" = from_hex('{locker_hex}') then amount else 0 end) as locked_supply
    from transfers
)
select
    (mb.minted - mb.burned) as circulating_supply,
    lb.locked_supply,
    lb.locked_supply * 1.0 / nullif(mb.minted - mb.burned, 0) as pct_locked
from mint_burn mb
cross join locker_balance lb
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
