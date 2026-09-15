# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
MIN_HOLD = "{{min_hold}}"
MAX_SELL_PCT = "{{max_sell_pct}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    min_hold_val = float(MIN_HOLD)
    max_sell_pct_val = float(MAX_SELL_PCT)
except ValueError:
    raise ValueError(f"Invalid min_hold/max_sell_pct: {MIN_HOLD!r}, {MAX_SELL_PCT!r}")
if min_hold_val < 0:
    raise ValueError(f"min_hold must be >= 0: {MIN_HOLD!r}")
if not (0 <= max_sell_pct_val <= 1):
    raise ValueError(f"max_sell_pct must be between 0 and 1: {MAX_SELL_PCT!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# Per-wallet continuous score (not a binary label, unlike diamond_hands_classifier,
# and not an aggregate %, unlike diamond_hands_percentage): rewards a low
# sell-to-buy ratio and a large net balance, log-dampened so whales don't
# swamp the ranking on size alone.
sql = f"""
with movements as (
    select "to" as wallet, amount as amt, amount as bought, 0.0 as sold
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select "from" as wallet, -amount as amt, 0.0 as bought, amount as sold
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
),
wallet_stats as (
    select
        wallet,
        sum(amt) as net_balance,
        sum(bought) as total_bought,
        sum(sold) as total_sold
    from movements
    group by wallet
    having sum(bought) > 0
),
scored as (
    select
        wallet,
        net_balance,
        total_sold / total_bought as sell_ratio,
        (1 - (total_sold / total_bought)) * ln(1 + greatest(net_balance, 0)) as diamond_score
    from wallet_stats
)
select
    concat('0x', to_hex(wallet)) as wallet_address,
    net_balance,
    sell_ratio,
    diamond_score
from scored
where net_balance >= {min_hold_val}
  and sell_ratio <= {max_sell_pct_val}
order by diamond_score desc
limit 1000
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
