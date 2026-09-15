# Sandworm Power Toolbox — {{__tool_name}}
import re

SYMBOL_A = "{{symbol_a}}"
SYMBOL_B = "{{symbol_b}}"
CHAIN = "{{chain}}"
INTERVAL = "{{interval}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
SYMBOL_RE = re.compile(r"^[A-Za-z0-9._-]{1,20}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not SYMBOL_RE.match(SYMBOL_A):
    raise ValueError(f"Invalid symbol_a: {SYMBOL_A!r}")
if not SYMBOL_RE.match(SYMBOL_B):
    raise ValueError(f"Invalid symbol_b: {SYMBOL_B!r}")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")

sym_a = SYMBOL_A.upper().replace("'", "")
sym_b = SYMBOL_B.upper().replace("'", "")

sql = f"""
with a as (
    select date_trunc('{INTERVAL}', minute) as time, avg(price) as price_a
    from prices.usd
    where blockchain = '{CHAIN}' and symbol = '{sym_a}'
    group by 1
),
b as (
    select date_trunc('{INTERVAL}', minute) as time, avg(price) as price_b
    from prices.usd
    where blockchain = '{CHAIN}' and symbol = '{sym_b}'
    group by 1
)
select
    a.time,
    a.price_a / nullif(b.price_b, 0) as ratio
from a
join b on a.time = b.time
order by a.time
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
