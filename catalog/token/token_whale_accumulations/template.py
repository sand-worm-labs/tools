# Sandworm Power Toolbox — {{__tool_name}}
# "Solana transfers" reinterpreted as EVM ERC20 transfers, scanned across all
# tokens on the selected chain (no single contract_address input on this tool).
import json
import re

CHAIN = "{{chain}}"
THRESHOLD_PERCENTILE = "{{threshold_percentile}}".strip()
DATE_RANGE = json.loads("""{{date_range}}""")
TOP_N = "{{top_n}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
try:
    threshold_val = float(THRESHOLD_PERCENTILE) if THRESHOLD_PERCENTILE else 0.99
except ValueError:
    raise ValueError(f"Invalid threshold_percentile: {THRESHOLD_PERCENTILE!r}")
if not (0 < threshold_val < 1):
    raise ValueError(f"threshold_percentile must be between 0 and 1: {THRESHOLD_PERCENTILE!r}")

FROM_DATE, TO_DATE = str(DATE_RANGE.get("from", "")), str(DATE_RANGE.get("to", ""))
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
for label, value in (("date_range.from", FROM_DATE), ("date_range.to", TO_DATE)):
    if not DATE_RE.match(value):
        raise ValueError(f"Invalid {label}: {value!r}")
if FROM_DATE > TO_DATE:
    raise ValueError("date_range 'from' must not be after 'to'")

if TOP_N and not (TOP_N.isdigit() and int(TOP_N) > 0):
    raise ValueError(f"Invalid top_n: {TOP_N!r}")
top_n_val = int(TOP_N) if TOP_N else 10

sql = f"""
with priced as (
    select
        date_trunc('day', t.block_time) as day,
        t.contract_address,
        t.amount * coalesce(p.price, 0) as amount_usd
    from tokens.transfers t
    left join prices.usd p
        on p.blockchain = '{CHAIN}'
        and p.contract_address = t.contract_address
        and p.minute = date_trunc('minute', t.block_time)
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.block_time >= date('{FROM_DATE}')
      and t.block_time < date('{TO_DATE}') + interval '1' day
),
thresholds as (
    select
        contract_address,
        day,
        approx_percentile(amount_usd, {threshold_val}) as whale_threshold
    from priced
    group by 1, 2
),
whales as (
    select p.contract_address, p.day
    from priced p
    join thresholds th on th.contract_address = p.contract_address and th.day = p.day
    where th.whale_threshold > 0 and p.amount_usd >= th.whale_threshold
)
select
    day,
    to_hex(contract_address) as token_address,
    count(*) as whale_count
from whales
group by 1, 2
order by day desc, whale_count desc
limit {top_n_val}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
