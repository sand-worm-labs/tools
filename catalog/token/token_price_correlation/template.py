# Sandworm Power Toolbox — {{__tool_name}}
import re

TOKEN1 = "{{token1}}"
TOKEN2 = "{{token2}}"
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
SYMBOL_RE = re.compile(r"^[A-Za-z0-9._-]{1,20}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not SYMBOL_RE.match(TOKEN1):
    raise ValueError(f"Invalid token1: {TOKEN1!r}")
if not SYMBOL_RE.match(TOKEN2):
    raise ValueError(f"Invalid token2: {TOKEN2!r}")

token1_sym = TOKEN1.upper().replace("'", "")
token2_sym = TOKEN2.upper().replace("'", "")

# "Rolling correlation" implemented as a 30-day trailing window via corr()
# as a window function, ordered by date.
sql = f"""
with p1 as (
    select date_trunc('day', minute) as day, avg(price) as price1
    from prices.usd
    where blockchain = '{CHAIN}' and symbol = '{token1_sym}'
    group by 1
),
p2 as (
    select date_trunc('day', minute) as day, avg(price) as price2
    from prices.usd
    where blockchain = '{CHAIN}' and symbol = '{token2_sym}'
    group by 1
),
joined as (
    select p1.day as date, p1.price1, p2.price2
    from p1
    join p2 on p1.day = p2.day
)
select
    date,
    price1 as token1_price,
    price2 as token2_price,
    corr(price1, price2) over (order by date rows between 29 preceding and current row) as correlation
from joined
order by date
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
