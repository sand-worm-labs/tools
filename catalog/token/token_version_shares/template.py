# Sandworm Power Toolbox — {{__tool_name}}

CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if LOOKBACK_DAYS and (not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

lookback = LOOKBACK_DAYS if LOOKBACK_DAYS else "30"

# EVM equivalent of Solana's SPL vs Token-2022 standard split: adoption
# shares across ERC20/ERC721/ERC1155. "Creation" is approximated as each
# contract's first transfer seen within the lookback window (there is no
# reliable cross-chain contract-creation table in the decoded tokens schema),
# so a token that existed but was inactive before the window is counted as
# newly created at its first in-window transfer.
sql = f"""
with first_seen as (
    select contract_address, token_standard, min(block_time) as first_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{lookback}' day
      and token_standard in ('erc20', 'erc721', 'erc1155')
    group by contract_address, token_standard
),
daily as (
    select
        cast(date_trunc('day', first_time) as varchar) as period,
        token_standard as token_version,
        count(distinct contract_address) as tokens_created
    from first_seen
    group by 1, 2
)
select
    period,
    token_version,
    tokens_created,
    tokens_created * 1.0 / sum(tokens_created) over (partition by period) as share
from daily
order by period, token_version
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
