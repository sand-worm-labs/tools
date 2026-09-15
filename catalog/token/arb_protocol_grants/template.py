# Sandworm Power Toolbox — {{__tool_name}}
import json
import re
from datetime import datetime

CHAIN = "{{chain}}"
TREASURY_ADDRESS = "{{treasury_address}}"
CATEGORY = "{{category}}".strip()
DATE_RANGE = """{{date_range}}"""

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
# ARB token contract, native to Arbitrum One; the query is chain-selectable
# but only returns rows when chain='arbitrum' since that's the token's home chain.
ARB_TOKEN_ADDRESS = "0x912CE59144191C1204E64559FE8253a0e49E6548"

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TREASURY_ADDRESS):
    raise ValueError(f"Invalid treasury_address: {TREASURY_ADDRESS!r}")
try:
    date_range = json.loads(DATE_RANGE)
    date_from = str(date_range["from"]).strip()
    date_to = str(date_range["to"]).strip()
    datetime.strptime(date_from, "%Y-%m-%d")
    datetime.strptime(date_to, "%Y-%m-%d")
except (json.JSONDecodeError, KeyError, ValueError):
    raise ValueError(f"Invalid date_range: {DATE_RANGE!r}")

treasury_hex = TREASURY_ADDRESS[2:].lower()
arb_hex = ARB_TOKEN_ADDRESS[2:].lower()
category_filter = ""
if CATEGORY:
    escaped_category = CATEGORY.replace("'", "''")
    category_filter = f"and lower(coalesce(l.category, '')) = lower('{escaped_category}')"

sql = f"""
with grants as (
    select "to" as recipient, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{arb_hex}')
      and "from" = from_hex('{treasury_hex}')
      and block_time >= date '{date_from}'
      and block_time < date '{date_to}' + interval '1' day
),
labeled as (
    select
        coalesce(l.name, '0x' || to_hex(g.recipient)) as protocol,
        coalesce(l.category, 'uncategorized') as category,
        g.amt
    from grants g
    left join labels.addresses l on l.address = g.recipient and l.blockchain = '{CHAIN}'
)
select
    protocol,
    category,
    sum(amt) as total_amount,
    count(*) as grant_count
from labeled
where 1 = 1 {category_filter}
group by protocol, category
order by total_amount desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
