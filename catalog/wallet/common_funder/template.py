# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLETS = "{{wallets}}"
DAYS = "{{days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DAYS.isdigit() or int(DAYS) <= 0:
    raise ValueError(f"Invalid days: {DAYS!r}")

wallets = [w.strip() for w in WALLETS.split(",") if w.strip()]
if not wallets:
    raise ValueError("At least one target address is required")
for w in wallets:
    if not ADDRESS_RE.match(w):
        raise ValueError(f"Invalid wallet in wallets: {w!r}")

wallet_hexes = [w[2:].lower() for w in wallets]
targets_values = ", ".join(f"(from_hex('{h}'))" for h in wallet_hexes)

sql = f"""
with targets as (
    select wallet from (values {targets_values}) as t(wallet)
),
funding_txs as (
    select
        t."to" as wallet,
        t."from" as funder,
        t.block_time,
        row_number() over (partition by t."to" order by t.block_time asc) as rn
    from {CHAIN}.transactions t
    join targets g on t."to" = g.wallet
    where t.value > uint256 '0'
      and t.block_time >= now() - interval '{DAYS}' day
)
select
    '0x' || to_hex(funder) as funder,
    count(distinct wallet) as funded_count
from funding_txs
where rn = 1
group by funder
having count(distinct wallet) >= 2
order by funded_count desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
