# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# Single aggregate row across all buyer wallets (unlike diamond_hands_classifier's
# per-wallet label or diamond_hand_scorer's per-wallet numeric score): the
# overall share of ever-buyers who never sold and still hold a balance.
sql = f"""
with movements as (
    select "to" as wallet, amount as amt, 0 as is_sell
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select "from" as wallet, -amount as amt, 1 as is_sell
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
),
wallet_stats as (
    select
        wallet,
        sum(amt) as net_balance,
        sum(is_sell) as sell_events
    from movements
    group by wallet
    having sum(case when is_sell = 0 then amt else 0 end) > 0
),
classified as (
    select case when sell_events = 0 and net_balance > 0 then 1 else 0 end as is_diamond
    from wallet_stats
)
select
    sum(is_diamond) as diamond_hands,
    count(*) - sum(is_diamond) as sold,
    100.0 * sum(is_diamond) / nullif(count(*), 0) as percentage
from classified
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
