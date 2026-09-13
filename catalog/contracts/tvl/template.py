# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS}' DAY"
limit_clause = f"limit {LIMIT}" if LIMIT else ""

# Balance is derived as a running net of all historical in/out value, not a
# balance snapshot table, so a non-"all" time range shows the net change
# within that window rather than the contract's true absolute balance. ETH
# is kept in native units (no reliable native-asset row on prices.usd to
# convert against); ERC20 balances are blended into one USD figure since
# summing raw amounts across different tokens isn't meaningful.
sql = f"""
with eth_flow as (
    select
        date_trunc('day', block_time) as day,
        sum(case
            when "to" = from_hex('{contract_hex}') then value
            when "from" = from_hex('{contract_hex}') then -value
            else 0
        end) as net_eth
    from {CHAIN}.traces
    where type = 'call'
      and value > 0
      and "from" != "to"
      and ("to" = from_hex('{contract_hex}') or "from" = from_hex('{contract_hex}'))
      {time_where}
    group by 1
),
token_flow as (
    select
        date_trunc('day', t.block_time) as day,
        sum(
            (case
                when t."to" = from_hex('{contract_hex}') then t.amount
                when t."from" = from_hex('{contract_hex}') then -t.amount
                else 0
            end) * coalesce(p.price, 0)
        ) as net_token_usd
    from tokens.transfers t
    left join prices.usd p
        on p.blockchain = '{CHAIN}'
        and p.contract_address = t.contract_address
        and p.minute = date_trunc('minute', t.block_time)
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t."from" != t."to"
      and (t."to" = from_hex('{contract_hex}') or t."from" = from_hex('{contract_hex}'))
      {time_where}
    group by 1
),
combined as (
    select
        coalesce(e.day, k.day) as day,
        coalesce(e.net_eth, 0) as net_eth,
        coalesce(k.net_token_usd, 0) as net_token_usd
    from eth_flow e
    full outer join token_flow k on e.day = k.day
)
select
    day,
    sum(net_eth) over (order by day) / 1e18 as eth_balance,
    sum(net_token_usd) over (order by day) as token_balance_usd
from combined
order by day desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y=["eth_balance", "token_balance_usd"])
fig.show()

{{__df_name}}
