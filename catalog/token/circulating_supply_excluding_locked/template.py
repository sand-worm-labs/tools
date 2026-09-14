# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

# No dedicated table of Balancer's veBAL/vesting lock contracts is verified
# here, so "locked" is approximated: any address that has only ever received
# this token and never sent it out behaves like a lock/vesting sink (a normal
# holder eventually transacts). This heuristic is generic and works for any
# ERC20, not just BAL.
sql = f"""
with transfers as (
    select block_time, "from" as addr, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and "from" <> from_hex('0000000000000000000000000000000000000000')
    union all
    select block_time, "to" as addr, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
),
mint_burn as (
    select date_trunc('day', block_time) as day,
        sum(case when "from" = from_hex('0000000000000000000000000000000000000000') then amount else 0 end) as minted,
        sum(case when "to" in (from_hex('0000000000000000000000000000000000000000'), from_hex('000000000000000000000000000000000000dead')) then amount else 0 end) as burned
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
    group by 1
),
daily_supply as (
    select day, sum(minted - burned) over (order by day) as total_supply
    from mint_burn
),
never_senders as (
    select addr
    from transfers
    group by addr
    having sum(case when amt < 0 then 1 else 0 end) = 0
),
locked_daily as (
    select date_trunc('day', t.block_time) as day, sum(t.amt) as net
    from transfers t
    join never_senders n on n.addr = t.addr
    group by 1
),
locked_running as (
    select day, sum(net) over (order by day) as locked_supply
    from locked_daily
)
select
    s.day,
    s.total_supply - coalesce(l.locked_supply, 0) as circ_supply,
    coalesce(l.locked_supply, 0) as locked_supply
from daily_supply s
left join locked_running l on l.day = s.day
order by s.day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
