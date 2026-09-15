# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
STAKING_CONTRACT = "{{staking_contract}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if STAKING_CONTRACT and not ADDRESS_RE.match(STAKING_CONTRACT):
    raise ValueError(f"Invalid staking_contract: {STAKING_CONTRACT!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
# When a staking_contract is given, transfers to/from it are dropped entirely
# rather than netted normally, so staked tokens keep counting toward the
# original holder's balance instead of vanishing into the staking contract.
staking_filter = ""
if STAKING_CONTRACT:
    staking_hex = STAKING_CONTRACT[2:].lower()
    staking_filter = f"and \"from\" != from_hex('{staking_hex}') and \"to\" != from_hex('{staking_hex}')"

sql = f"""
with movements as (
    select "to" as wallet, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      {staking_filter}
    union all
    select "from" as wallet, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      {staking_filter}
),
balances as (
    select wallet, sum(amt) as balance_raw
    from movements
    group by wallet
    having sum(amt) > 0
),
scaled as (
    select b.balance_raw / power(10, coalesce(e.decimals, 18)) as balance
    from balances b
    left join tokens.erc20 e
        on e.blockchain = '{CHAIN}' and e.contract_address = from_hex('{token_hex}')
)
select
    approx_percentile(balance, 0.2) as p20,
    approx_percentile(balance, 0.4) as p40,
    approx_percentile(balance, 0.6) as p60,
    approx_percentile(balance, 0.8) as p80
from scaled
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
