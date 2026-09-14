# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
TOP_N = "{{top_n}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if TOP_N and not (TOP_N.isdigit() and int(TOP_N) > 0):
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

limit_clause = f"limit {TOP_N}" if TOP_N else ""

# "NTILE for top quintile": rank all ERC20 participants on the chain by
# send+receive count, keep only the top 20% (quintile 5), then order by count.
sql = f"""
with participants as (
    select "from" as wallet from tokens.transfers where blockchain = '{CHAIN}'
    union all
    select "to" as wallet from tokens.transfers where blockchain = '{CHAIN}'
),
counts as (
    select wallet, count(*) as transaction_count
    from participants
    group by 1
),
ranked as (
    select wallet, transaction_count, ntile(5) over (order by transaction_count) as quintile
    from counts
)
select to_hex(wallet) as participant, transaction_count
from ranked
where quintile = 5
order by transaction_count desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
