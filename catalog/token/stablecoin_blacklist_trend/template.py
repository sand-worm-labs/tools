# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Canonical native-issuance deployments only (not bridged wrapped copies).
USDC_ADDRESSES = {
    "ethereum": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "base": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
    "optimism": "0x0b2c639c533813f4aa9d7837caf62653d097ff85",
    "arbitrum": "0xaf88d065e77c8cc2239327c5edb3a432268e5831",
    "polygon": "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",
    "avalanche": "0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e",
    "celo": "0xceba9300f2b948710d2653dd7b07f33a8b32118c",
}
USDT_ADDRESSES = {
    "ethereum": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "polygon": "0xc2132d05d31c914a87c6611c10748aeb04b58e8f",
    "bsc": "0x55d398326f99059ff775485246999027b3197955",
    "avalanche": "0x9702230a8ea53601f5cd2dc00fdbc13d4df4a8c7",
    "arbitrum": "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9",
    "optimism": "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if CHAIN not in USDC_ADDRESSES and CHAIN not in USDT_ADDRESSES:
    raise ValueError(f"No known native USDC or USDT deployment tracked for chain {CHAIN!r}")

date_filter = f"and evt_block_time >= date('{DATE_FROM}')" if DATE_FROM else ""

# Assumes Dune Spellbook's standard per-contract decoded-event table naming
# (`<project>_<chain>.<Contract>_evt_<Event>`) for USDC's real `Blacklisted`
# and USDT's real `AddedBlackList` events.
usdc_cte = (
    f"select evt_block_time, _account as address from usdc_{CHAIN}.FiatTokenV2_2_evt_Blacklisted where 1=1 {date_filter}"
    if CHAIN in USDC_ADDRESSES
    else "select cast(null as timestamp) as evt_block_time, cast(null as varbinary) as address where 1=0"
)
usdt_cte = (
    f"select evt_block_time, _user as address from tether_{CHAIN}.TetherToken_evt_AddedBlackList where 1=1 {date_filter}"
    if CHAIN in USDT_ADDRESSES
    else "select cast(null as timestamp) as evt_block_time, cast(null as varbinary) as address where 1=0"
)

sql = f"""
with usdc_events as (
    {usdc_cte}
),
usdt_events as (
    {usdt_cte}
),
usdc_monthly as (
    select date_trunc('month', evt_block_time) as month, count(distinct address) as usdc_wallets
    from usdc_events
    group by 1
),
usdt_monthly as (
    select date_trunc('month', evt_block_time) as month, count(distinct address) as usdt_wallets
    from usdt_events
    group by 1
)
select
    coalesce(c.month, t.month) as month,
    coalesce(c.usdc_wallets, 0) as usdc_wallets,
    coalesce(t.usdt_wallets, 0) as usdt_wallets
from usdc_monthly c
full outer join usdt_monthly t on t.month = c.month
order by month
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
