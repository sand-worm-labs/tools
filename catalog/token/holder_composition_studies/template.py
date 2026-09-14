# Sandworm Power Toolbox — {{__tool_name}}
import json
import re

CONTRACT_ADDRESS = "{{contract_address}}"
DATE_RANGE = json.loads("""{{date_range}}""")
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

FROM_DATE, TO_DATE = str(DATE_RANGE.get("from", "")), str(DATE_RANGE.get("to", ""))
for label, value in (("date_range.from", FROM_DATE), ("date_range.to", TO_DATE)):
    if not DATE_RE.match(value):
        raise ValueError(f"Invalid {label}: {value!r}")
if FROM_DATE > TO_DATE:
    raise ValueError("date_range 'from' must not be after 'to'")

token_hex = CONTRACT_ADDRESS[2:].lower()

# "Studies" = lookback windows ending at date_range.to over which each current
# holder's activity is checked (closest EVM-native reading of the original
# LP/aToken-composition ask: which holders "acted" in the last N days).
sql = f"""
with movements as (
    select "to" as wallet, amount as amt, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and block_time < date('{TO_DATE}') + interval '1' day
      and block_time >= date('{FROM_DATE}')
    union all
    select "from" as wallet, -amount as amt, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and block_time < date('{TO_DATE}') + interval '1' day
      and block_time >= date('{FROM_DATE}')
),
holders as (
    select wallet, sum(amt) as balance
    from movements
    group by wallet
    having sum(amt) > 0
),
last_activity as (
    select wallet, max(block_time) as last_seen
    from movements
    group by wallet
),
per_study as (
    select '7d' as study, h.wallet, (a.last_seen >= date('{TO_DATE}') - interval '7' day) as acted_flag
    from holders h join last_activity a on a.wallet = h.wallet
    union all
    select '30d' as study, h.wallet, (a.last_seen >= date('{TO_DATE}') - interval '30' day) as acted_flag
    from holders h join last_activity a on a.wallet = h.wallet
    union all
    select '90d' as study, h.wallet, (a.last_seen >= date('{TO_DATE}') - interval '90' day) as acted_flag
    from holders h join last_activity a on a.wallet = h.wallet
)
select
    study,
    acted_flag,
    100.0 * count(*) / sum(count(*)) over (partition by study) as holder_pct
from per_study
group by study, acted_flag
order by study, acted_flag desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
