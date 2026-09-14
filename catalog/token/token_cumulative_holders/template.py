# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}".strip()
CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
date_from_filter = f"where date >= date('{DATE_FROM}')" if DATE_FROM else ""

# "Holder" here means an address that has ever received the token (cumulative
# reach), not necessarily one still holding a non-zero balance — that
# current-balance definition lives in token_holder_count / _historical.
# cumulative_holders is computed over full history so a date_from filter
# trims the displayed window without understating the running total.
sql = f"""
with first_seen as (
    select "to" as address, min(block_date) as first_date
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{token_hex}')
    group by "to"
),
daily_new as (
    select first_date as date, count(*) as new_holders
    from first_seen
    group by first_date
),
running as (
    select
        date,
        new_holders as daily_new,
        sum(new_holders) over (order by date) as cumulative_holders
    from daily_new
)
select date, daily_new, cumulative_holders
from running
{date_from_filter}
order by date
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
