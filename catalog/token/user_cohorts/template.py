# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
COHORT_BLOCKS = "{{cohort_blocks}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

boundaries = []
if COHORT_BLOCKS:
    for part in COHORT_BLOCKS.split(","):
        part = part.strip()
        if not part.isdigit():
            raise ValueError(f"Invalid cohort_blocks entry: {part!r}")
        boundaries.append(int(part))
    boundaries = sorted(set(boundaries))

contract_hex = CONTRACT_ADDRESS[2:].lower()

if boundaries:
    when_clauses = "\n        ".join(
        f"when first_block < {b} then 'cohort_{i + 1} (< block {b})'" for i, b in enumerate(boundaries)
    )
    cohort_expr = f"""case
        {when_clauses}
        else 'cohort_{len(boundaries) + 1} (>= block {boundaries[-1]})'
    end"""
else:
    # No explicit boundaries supplied: fall back to even quartiles over the
    # contract's own observed first-interaction blocks.
    cohort_expr = "concat('Q', cast(ntile(4) over (order by first_block) as varchar))"

sql = f"""
with first_seen as (
    select wallet, min(block_number) as first_block
    from (
        select "to" as wallet, block_number
        from tokens.transfers
        where blockchain = '{CHAIN}'
          and token_standard = 'erc20'
          and contract_address = from_hex('{contract_hex}')
        union all
        select "from" as wallet, block_number
        from tokens.transfers
        where blockchain = '{CHAIN}'
          and token_standard = 'erc20'
          and contract_address = from_hex('{contract_hex}')
    ) t
    group by wallet
),
cohorted as (
    select
        wallet,
        first_block,
        {cohort_expr} as cohort
    from first_seen
)
select
    cohort,
    count(*) as user_count,
    min(first_block) as first_block
from cohorted
group by cohort
order by first_block
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
