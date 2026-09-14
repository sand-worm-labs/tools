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
CONTRACT_ADDRESS = "{{contract_address}}"
PRICE_THRESHOLD = "{{price_threshold}}"
DATE_FROM, DATE_TO = _parse_date_range("""{{date_range}}""")

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not PRICE_THRESHOLD.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid price_threshold: {PRICE_THRESHOLD!r}")
if not DATE_FROM or not DATE_TO:
    raise ValueError("date_range requires both 'from' and 'to'")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with buys as (
    select
        taker,
        amount_usd,
        token_bought_amount,
        amount_usd / nullif(token_bought_amount, 0) as price
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address = from_hex('{token_hex}')
      and block_date >= date('{DATE_FROM}')
      and block_date <= date('{DATE_TO}')
)
select
    to_hex(taker) as wallet,
    sum(amount_usd) as total_usd,
    sum(token_bought_amount) as total_tokens,
    avg(price) as avg_price
from buys
where price <= {PRICE_THRESHOLD}
group by taker
order by total_usd desc
limit 500
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
