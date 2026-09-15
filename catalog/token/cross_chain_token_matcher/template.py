# Sandworm Power Toolbox — {{__tool_name}}
CHAIN_A = "{{chain_a}}"
CHAIN_B = "{{chain_b}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN_A not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain_a: {CHAIN_A!r}")
if CHAIN_B not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain_b: {CHAIN_B!r}")
if CHAIN_A == CHAIN_B:
    raise ValueError("chain_a and chain_b must differ")
if LOOKBACK_DAYS and (not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

lookback_days = int(LOOKBACK_DAYS) if LOOKBACK_DAYS else 30

sql = f"""
with active_a as (
    select distinct contract_address
    from tokens.transfers
    where blockchain = '{CHAIN_A}'
      and token_standard = 'erc20'
      and block_time >= now() - interval '{lookback_days}' day
),
active_b as (
    select distinct contract_address
    from tokens.transfers
    where blockchain = '{CHAIN_B}'
      and token_standard = 'erc20'
      and block_time >= now() - interval '{lookback_days}' day
)
select
    a.symbol,
    a.decimals,
    a.blockchain as blockchain_a,
    '0x' || to_hex(a.contract_address) as contract_a,
    b.blockchain as blockchain_b,
    '0x' || to_hex(b.contract_address) as contract_b
from tokens.erc20 a
join tokens.erc20 b
    on upper(a.symbol) = upper(b.symbol)
    and a.decimals = b.decimals
join active_a aa on aa.contract_address = a.contract_address
join active_b bb on bb.contract_address = b.contract_address
where a.blockchain = '{CHAIN_A}'
  and b.blockchain = '{CHAIN_B}'
order by a.symbol
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
