# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS:
    LOOKBACK_DAYS = "30"
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

zero_hex = "0" * 40

# EVM generalization: this catalog is EVM-only, so "fungible token" creation
# (originally a Solana mint-account concept) is approximated as an ERC20
# contract's first-ever mint transfer (from the zero address) — its launch.
sql = f"""
with first_mint as (
    select contract_address, min(date_trunc('day', block_time)) as dt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and "from" = from_hex('{zero_hex}')
    group by contract_address
),
daily as (
    select dt, count(*) as daily_tokens
    from first_mint
    group by dt
),
cumulative as (
    select dt, daily_tokens, sum(daily_tokens) over (order by dt) as total_tokens
    from daily
)
select dt, daily_tokens, total_tokens
from cumulative
where dt >= now() - interval '{LOOKBACK_DAYS}' day
order by dt
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
