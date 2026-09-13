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

# Native-ETH inflows come from the trace-level value transfers (this also
# covers plain top-level ETH sends, which surface as a trace with an empty
# trace_address); ERC20 inflows come from tokens.transfers, priced in USD via
# prices.usd since summing raw token amounts across different tokens isn't
# meaningful. Self-transfers are excluded on both sides so a contract sending
# itself value doesn't inflate revenue.
sql = f"""
with eth_in as (
    select
        date_trunc('day', block_time) as day,
        sum(value) / 1e18 as eth_in
    from {CHAIN}.traces
    where type = 'call'
      and value > 0
      and "to" = from_hex('{contract_hex}')
      and "from" != from_hex('{contract_hex}')
      {time_where}
    group by 1
),
token_in as (
    select
        date_trunc('day', t.block_time) as day,
        sum(t.amount * coalesce(p.price, 0)) as token_in_usd
    from tokens.transfers t
    left join prices.usd p
        on p.blockchain = '{CHAIN}'
        and p.contract_address = t.contract_address
        and p.minute = date_trunc('minute', t.block_time)
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t."to" = from_hex('{contract_hex}')
      and t."from" != from_hex('{contract_hex}')
      {time_where}
    group by 1
)
select
    coalesce(e.day, k.day) as day,
    coalesce(e.eth_in, 0) as eth_in,
    coalesce(k.token_in_usd, 0) as token_in_usd
from eth_in e
full outer join token_in k on e.day = k.day
order by day desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="day", y=["eth_in", "token_in_usd"])
fig.show()

{{__df_name}}
