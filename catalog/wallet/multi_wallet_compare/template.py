# Sandworm Power Toolbox — {{__tool_name}}
import json
import re

CHAIN = "{{chain}}"
WALLETS_RAW = "{{wallets}}".strip()
DAYS = "{{days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DAYS.isdigit() or int(DAYS) <= 0:
    raise ValueError(f"Invalid days: {DAYS!r}")

try:
    parsed = json.loads(WALLETS_RAW) if WALLETS_RAW.startswith("[") else WALLETS_RAW.split(",")
except (json.JSONDecodeError, ValueError):
    parsed = WALLETS_RAW.split(",")
WALLETS = [w.strip() for w in parsed if str(w).strip()]

if not WALLETS:
    raise ValueError("wallets is required")
for w in WALLETS:
    if not ADDRESS_RE.match(w):
        raise ValueError(f"Invalid wallet address: {w!r}")

wallet_values = ", ".join(f"from_hex('{w[2:].lower()}')" for w in WALLETS)

sql = f"""
with movements as (
    select "from" as wallet, "to" as counterparty, amount, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and "from" in ({wallet_values})
      and block_time >= now() - interval '{DAYS}' day
    union all
    select "to" as wallet, "from" as counterparty, amount, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and "to" in ({wallet_values})
      and block_time >= now() - interval '{DAYS}' day
)
select
    wallet,
    count(*) as transfer_count,
    sum(amount) as total_amount,
    count(distinct counterparty) as unique_counterparties,
    min(block_time) as first_activity,
    max(block_time) as last_activity
from movements
group by wallet
order by transfer_count desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
