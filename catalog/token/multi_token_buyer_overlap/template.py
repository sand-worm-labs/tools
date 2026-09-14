# Sandworm Power Toolbox — {{__tool_name}}
import json
import re


def _parse_date_range(raw):
    raw = raw.strip()
    if not raw:
        return None, None
    try:
        d = json.loads(raw)
        return d.get("from") or None, d.get("to") or None
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None, None


CHAIN = "{{chain}}"
TOKEN1 = "{{contract_address}}"
TOKEN2 = "{{token_b_address}}"
MIN_USD = "{{min_usd}}".strip()
DATE_FROM, DATE_TO = _parse_date_range("""{{date_range}}""")

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN1):
    raise ValueError(f"Invalid contract_address: {TOKEN1!r}")
if not ADDRESS_RE.match(TOKEN2):
    raise ValueError(f"Invalid token_b_address: {TOKEN2!r}")
if not MIN_USD.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")

token1_hex = TOKEN1[2:].lower()
token2_hex = TOKEN2[2:].lower()
date_from_clause = f"and block_time >= date('{DATE_FROM}')" if DATE_FROM else "and block_time >= now() - interval '90' day"
date_to_clause = f"and block_time <= date('{DATE_TO}')" if DATE_TO else ""

sql = f"""
with buys_a as (
    select taker as wallet, sum(amount_usd) as usd_a
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address = from_hex('{token1_hex}')
      {date_from_clause} {date_to_clause}
    group by 1
    having sum(amount_usd) >= {MIN_USD}
),
buys_b as (
    select taker as wallet, sum(amount_usd) as usd_b
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address = from_hex('{token2_hex}')
      {date_from_clause} {date_to_clause}
    group by 1
    having sum(amount_usd) >= {MIN_USD}
)
select
    a.wallet,
    a.usd_a as token1_usd,
    b.usd_b as token2_usd,
    a.usd_a + b.usd_b as overlap_usd
from buys_a a
join buys_b b on a.wallet = b.wallet
order by overlap_usd desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
