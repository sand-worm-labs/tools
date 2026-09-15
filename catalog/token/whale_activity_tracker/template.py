# Sandworm Power Toolbox — {{__tool_name}}
# "tokens_solana.transfers" reinterpreted as this catalog's EVM tokens.transfers,
# since this catalog is EVM-only.
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
THRESHOLD_MULTIPLIER = "{{threshold_multiplier}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    multiplier_val = float(THRESHOLD_MULTIPLIER) if THRESHOLD_MULTIPLIER else 10.0
except ValueError:
    raise ValueError(f"Invalid threshold_multiplier: {THRESHOLD_MULTIPLIER!r}")
if multiplier_val <= 0:
    raise ValueError(f"threshold_multiplier must be > 0: {THRESHOLD_MULTIPLIER!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with recent_transfers as (
    select block_time, "from" as from_wallet, "to" as to_wallet, amount
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and block_time >= now() - interval '90' day
),
stats as (
    select avg(amount) as avg_amount
    from recent_transfers
),
whale_txns as (
    select
        date_trunc('day', t.block_time) as day,
        t.to_wallet,
        t.from_wallet,
        t.amount
    from recent_transfers t
    cross join stats s
    where t.amount > s.avg_amount * {multiplier_val}
)
select day as date, to_hex(to_wallet) as wallet, amount, 'buy' as action from whale_txns
union all
select day as date, to_hex(from_wallet) as wallet, amount, 'sell' as action from whale_txns
order by date desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
