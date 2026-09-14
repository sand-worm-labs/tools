# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
START_BLOCK = "{{start_block}}"
TOP_N = "{{top_n}}".strip() or "100"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not START_BLOCK.isdigit():
    raise ValueError(f"Invalid start_block: {START_BLOCK!r}")
if not TOP_N.isdigit() or int(TOP_N) <= 0:
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# Retention is defined as still holding at least half of the initial buy
# amount, since there is no separate retention-threshold input.
sql = f"""
with buys as (
    select taker, token_bought_amount as amount, block_number, block_time
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address = from_hex('{token_hex}')
      and block_number >= {START_BLOCK}
),
ranked_buys as (
    select taker, amount, block_time,
        row_number() over (partition by taker order by block_time asc) as rn
    from buys
),
first_buys as (
    select taker, amount as initial_balance, block_time as first_buy_time
    from ranked_buys
    where rn = 1
),
selected as (
    select taker, initial_balance
    from (
        select taker, initial_balance,
            row_number() over (order by first_buy_time asc) as buyer_rank
        from first_buys
    ) t
    where buyer_rank <= {TOP_N}
),
inflows as (
    select "to" as addr, sum(amount) as amt
    from tokens.transfers
    where blockchain = '{CHAIN}' and contract_address = from_hex('{token_hex}')
    group by 1
),
outflows as (
    select "from" as addr, sum(amount) as amt
    from tokens.transfers
    where blockchain = '{CHAIN}' and contract_address = from_hex('{token_hex}')
    group by 1
)
select
    to_hex(s.taker) as address,
    s.initial_balance,
    coalesce(i.amt, 0) - coalesce(o.amt, 0) as current_hold,
    (coalesce(i.amt, 0) - coalesce(o.amt, 0)) >= (s.initial_balance * 0.5) as retention
from selected s
left join inflows i on i.addr = s.taker
left join outflows o on o.addr = s.taker
order by s.initial_balance desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
