# Sandworm Power Toolbox — {{__tool_name}}
# "Mint/accounts" (Solana jargon) reinterpreted as ERC20 contract_address /
# transfer participants, since this catalog is EVM-only.
import re

CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()
KEYWORDS_RAW = "{{keywords}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

keywords = [kw.strip().strip('"').strip("'").lower() for kw in (KEYWORDS_RAW or "ai,meme").split(",")]
keywords = [kw for kw in keywords if kw]
if not keywords:
    raise ValueError("At least one keyword is required")
if not all(re.match(r"^[a-z0-9 _-]{1,32}$", kw) for kw in keywords):
    raise ValueError(f"Invalid keywords: {KEYWORDS_RAW!r}")

match_clause = " or ".join(f"lower(e.name) like '%{kw}%' or lower(e.symbol) like '%{kw}%'" for kw in keywords)
theme_case = "\n        ".join(
    f"when lower(e.name) like '%{kw}%' or lower(e.symbol) like '%{kw}%' then '{kw}'" for kw in keywords
)

sql = f"""
with themed_tokens as (
    select
        e.contract_address,
        e.symbol,
        case
        {theme_case}
        end as theme
    from tokens.erc20 e
    where e.blockchain = '{CHAIN}'
      and ({match_clause})
)
select
    to_hex(t.contract_address) as token_address,
    t.symbol,
    t.theme,
    count(*) as tx_count,
    count(distinct tr."to") as unique_owners
from themed_tokens t
join tokens.transfers tr
    on tr.blockchain = '{CHAIN}'
    and tr.token_standard = 'erc20'
    and tr.contract_address = t.contract_address
where tr.block_time >= now() - interval '{LOOKBACK_DAYS}' day
group by t.contract_address, t.symbol, t.theme
order by tx_count desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
