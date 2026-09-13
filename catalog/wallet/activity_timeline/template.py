# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET = "{{wallet}}"
DAYS = "{{days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")
if not DAYS.isdigit() or int(DAYS) <= 0:
    raise ValueError(f"Invalid days: {DAYS!r}")

wallet_hex = WALLET[2:].lower()

sql = f"""
select
    date_trunc('day', block_time) as day,
    count(*) as tx_count,
    sum(case when "from" = from_hex('{wallet_hex}') then 1 else 0 end) as sent_count,
    sum(case when "to" = from_hex('{wallet_hex}') then 1 else 0 end) as received_count
from {CHAIN}.transactions
where ("from" = from_hex('{wallet_hex}') or "to" = from_hex('{wallet_hex}'))
  and block_time >= now() - interval '{DAYS}' day
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
