# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
MIN_HOLDINGS = "{{min_holdings}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    min_holdings_val = float(MIN_HOLDINGS) if MIN_HOLDINGS else 100.0
except ValueError:
    raise ValueError(f"Invalid min_holdings: {MIN_HOLDINGS!r}")
if min_holdings_val <= 0:
    raise ValueError(f"min_holdings must be > 0: {MIN_HOLDINGS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
tier_medium = min_holdings_val * 10
tier_large = min_holdings_val * 100
tier_whale = min_holdings_val * 1000

# Tiers are relative multiples of the caller-supplied min_holdings floor,
# not fixed absolute buckets — holders below that floor are dropped entirely.
sql = f"""
with movements as (
    select "to" as wallet, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select "from" as wallet, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
),
balances as (
    select wallet, sum(amt) as balance
    from movements
    group by wallet
    having sum(amt) >= {min_holdings_val}
),
tiered as (
    select
        case
            when balance < {tier_medium} then 'small'
            when balance < {tier_large} then 'medium'
            when balance < {tier_whale} then 'large'
            else 'whale'
        end as tier,
        balance
    from balances
)
select tier, count(*) as wallet_count, sum(balance) as total_holdings
from tiered
group by tier
order by min(balance)
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
