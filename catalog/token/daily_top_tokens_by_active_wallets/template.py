# Sandworm Power Toolbox — {{__tool_name}}
import json
import re

CHAIN = "{{chain}}"
DATE_RANGE = json.loads("""{{date_range}}""")
TOP_N = "{{top_n}}".strip() or "20"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")

DATE_FROM, DATE_TO = str(DATE_RANGE.get("from", "")), str(DATE_RANGE.get("to", ""))
for label, value in (("date_range.from", DATE_FROM), ("date_range.to", DATE_TO)):
    if not DATE_RE.match(value):
        raise ValueError(f"Invalid {label}: {value!r}")
if DATE_FROM > DATE_TO:
    raise ValueError("date_range 'from' must not be after 'to'")
if not TOP_N.isdigit() or int(TOP_N) <= 0:
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

# Chain-wide leaderboard across every ERC20 token, not a single contract —
# inherently a broad scan, bounded only by the date_range.
sql = f"""
with movements as (
    select date_trunc('day', block_time) as day, contract_address, "from" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and block_time >= date('{DATE_FROM}')
      and block_time < date('{DATE_TO}') + interval '1' day
    union all
    select date_trunc('day', block_time) as day, contract_address, "to" as wallet
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and block_time >= date('{DATE_FROM}')
      and block_time < date('{DATE_TO}') + interval '1' day
),
daily_active as (
    select day, contract_address, count(distinct wallet) as active_wallets
    from movements
    group by day, contract_address
),
ranked as (
    select
        day,
        contract_address,
        active_wallets,
        row_number() over (partition by day order by active_wallets desc) as rnk
    from daily_active
)
select
    r.day,
    coalesce(e.symbol, concat('0x', to_hex(r.contract_address))) as token,
    r.active_wallets
from ranked r
left join tokens.erc20 e on e.blockchain = '{CHAIN}' and e.contract_address = r.contract_address
where r.rnk <= {int(TOP_N)}
order by r.day desc, r.active_wallets desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
