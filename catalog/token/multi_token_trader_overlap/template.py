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
TOKEN1 = "{{token_address_1}}"
TOKEN2 = "{{token_address_2}}"
DATE_FROM, DATE_TO = _parse_date_range("""{{date_range}}""")

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN1):
    raise ValueError(f"Invalid token_address_1: {TOKEN1!r}")
if not ADDRESS_RE.match(TOKEN2):
    raise ValueError(f"Invalid token_address_2: {TOKEN2!r}")

token1_hex = TOKEN1[2:].lower()
token2_hex = TOKEN2[2:].lower()
date_from_clause = f"and block_time >= date('{DATE_FROM}')" if DATE_FROM else "and block_time >= now() - interval '90' day"
date_to_clause = f"and block_time <= date('{DATE_TO}')" if DATE_TO else ""

# "Trader" (vs. plain buyer) = wallet with both a buy and a sell leg on the
# token within the window, i.e. an active round-tripper rather than a holder.
sql = f"""
with trades_1 as (
    select taker as wallet,
        sum(amount_usd) filter (where token_bought_address = from_hex('{token1_hex}')) as bought_usd,
        count(*) filter (where token_sold_address = from_hex('{token1_hex}')) as sell_legs
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{token1_hex}') or token_sold_address = from_hex('{token1_hex}'))
      {date_from_clause} {date_to_clause}
    group by 1
    having count(*) filter (where token_sold_address = from_hex('{token1_hex}')) > 0
       and sum(amount_usd) filter (where token_bought_address = from_hex('{token1_hex}')) > 0
),
trades_2 as (
    select taker as wallet,
        sum(amount_usd) filter (where token_bought_address = from_hex('{token2_hex}')) as bought_usd,
        count(*) filter (where token_sold_address = from_hex('{token2_hex}')) as sell_legs
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{token2_hex}') or token_sold_address = from_hex('{token2_hex}'))
      {date_from_clause} {date_to_clause}
    group by 1
    having count(*) filter (where token_sold_address = from_hex('{token2_hex}')) > 0
       and sum(amount_usd) filter (where token_bought_address = from_hex('{token2_hex}')) > 0
)
select
    t1.wallet as trader_id,
    t1.bought_usd as total_bought_token1,
    t2.bought_usd as total_bought_token2
from trades_1 t1
join trades_2 t2 on t1.wallet = t2.wallet
order by total_bought_token1 + total_bought_token2 desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
