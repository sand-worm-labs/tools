# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if LOOKBACK_DAYS and (not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
time_where = f"and block_time >= now() - interval '{LOOKBACK_DAYS}' day" if LOOKBACK_DAYS else ""

# No dedicated foundation/vesting address list is supplied as input, so
# "non-circulating" is approximated as tokens moved to the zero address or
# the conventional 0x...dead burn address (mints/burns), the only
# non-circulating movement that is detectable generically from transfers
# alone without a curated address list.
sql = f"""
with transfers as (
    select block_time, "from", "to", amount
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      {time_where}
),
daily as (
    select
        date_trunc('day', block_time) as day,
        sum(case when "from" = from_hex('0000000000000000000000000000000000000000') then amount else 0 end) as minted,
        sum(case when "to" in (from_hex('0000000000000000000000000000000000000000'), from_hex('000000000000000000000000000000000000dead')) then amount else 0 end) as burned
    from transfers
    group by 1
)
select
    day,
    sum(minted - burned) over (order by day) as circulating_supply,
    burned as non_circulating_change
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
