# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CLAIM_CONTRACT = "{{claim_contract}}"
TOTAL_ELIGIBLE = "{{total_eligible}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CLAIM_CONTRACT):
    raise ValueError(f"Invalid claim_contract: {CLAIM_CONTRACT!r}")
if not TOTAL_ELIGIBLE.replace(".", "", 1).isdigit() or float(TOTAL_ELIGIBLE) <= 0:
    raise ValueError(f"Invalid total_eligible: {TOTAL_ELIGIBLE!r}")

claim_contract_hex = CLAIM_CONTRACT[2:].lower()

# claim_contract distributes claims for a single, protocol-specific token, so
# claims are modeled as any ERC20 transfer sent out of that contract.
sql = f"""
with claims as (
    select block_time, "to" as claimer
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and "from" = from_hex('{claim_contract_hex}')
),
first_claim as (
    select claimer, min(date_trunc('day', block_time)) as first_day
    from claims
    group by claimer
),
daily_new as (
    select first_day as day, count(*) as new_claimers
    from first_claim
    group by first_day
),
daily_activity as (
    select date_trunc('day', block_time) as day, count(*) as daily_claims
    from claims
    group by 1
)
select
    coalesce(a.day, n.day) as day,
    coalesce(n.new_claimers, 0) as daily_claimers,
    sum(coalesce(n.new_claimers, 0)) over (order by coalesce(a.day, n.day)) as total_claimers,
    cast(100.0 * sum(coalesce(n.new_claimers, 0)) over (order by coalesce(a.day, n.day)) / {TOTAL_ELIGIBLE} as varchar) as claimers_pct,
    coalesce(a.daily_claims, 0) as daily_claims,
    sum(coalesce(a.daily_claims, 0)) over (order by coalesce(a.day, n.day)) as total_claims
from daily_activity a
full outer join daily_new n on a.day = n.day
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
