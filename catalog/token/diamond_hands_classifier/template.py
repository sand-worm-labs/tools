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

# Per-wallet label: a "buyer" is any wallet that ever received the token.
# "diamond_hands" = never once sent it back out and still holds a positive
# balance; "paper_hands" = has sold at least once. (For the aggregate %
# across all holders, see diamond_hands_percentage; for a continuous score,
# see diamond_hand_scorer.)
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
    select
        wallet,
        net_balance,
        case when sell_events = 0 and net_balance > 0 then 'diamond_hands' else 'paper_hands' end as classification
    from wallet_stats
)
select
    concat('0x', to_hex(wallet)) as wallet_address,
    classification,
    net_balance
from classified
order by net_balance desc
limit 1000
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
