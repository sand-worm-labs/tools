# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN_ADDRESSES_RAW = "{{token_addresses}}".replace("[", "").replace("]", "").replace('"', "")
MIN_USD = "{{min_usd}}"
DATE_TO = "{{date_to}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

token_addresses = [a.strip() for a in TOKEN_ADDRESSES_RAW.split(",") if a.strip()]

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if len(token_addresses) < 2:
    raise ValueError("token_addresses requires at least 2 token addresses")
for a in token_addresses:
    if not ADDRESS_RE.match(a):
        raise ValueError(f"Invalid token address: {a!r}")
if not MIN_USD.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")
if DATE_TO and not DATE_RE.match(DATE_TO):
    raise ValueError(f"Invalid date_to: {DATE_TO!r}")

addr_in_list = ", ".join(f"from_hex('{a[2:].lower()}')" for a in token_addresses)
num_tokens = len(token_addresses)
date_where = f"and block_time < date '{DATE_TO}' + interval '1' day" if DATE_TO else ""

sql = f"""
with buys as (
    select taker as wallet, token_bought_address as token_address, sum(amount_usd) as usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address in ({addr_in_list})
      {date_where}
    group by 1, 2
),
qualifying as (
    select wallet, token_address, usd
    from buys
    where usd >= {MIN_USD}
)
select
    concat('0x', to_hex(wallet)) as wallet,
    array_join(array_agg(concat('0x', to_hex(token_address))), ',') as tokens_bought,
    sum(usd) as total_usd,
    count(distinct token_address) * 1.0 / {num_tokens} as overlap_score
from qualifying
group by wallet
having count(distinct token_address) >= 2
order by overlap_score desc, total_usd desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
