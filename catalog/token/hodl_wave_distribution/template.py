# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
SAMPLE_SIZE = "{{sample_size}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not SAMPLE_SIZE.isdigit() or int(SAMPLE_SIZE) <= 0:
    raise ValueError(f"Invalid sample_size: {SAMPLE_SIZE!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
sample_size_val = int(SAMPLE_SIZE)
lookback_days_val = int(LOOKBACK_DAYS)

# "HODL wave" for an ERC20 approximated as: among wallets that were active
# (sent or received the token) within the lookback window and still hold a
# positive balance, how long ago did each first acquire the token — bucketed
# by age_days rather than the coin-age/UTXO notion the term originates from.
sql = f"""
with movements as (
    select "to" as wallet, amount as amt, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
    union all
    select "from" as wallet, -amount as amt, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
),
balances as (
    select wallet, sum(amt) as balance
    from movements
    group by wallet
    having sum(amt) > 0
),
recent_active as (
    select distinct wallet
    from movements
    where block_time >= now() - interval '{lookback_days_val}' day
),
activity as (
    select wallet, min(block_time) as first_tx, max(block_time) as last_tx
    from movements
    group by wallet
)
select
    a.wallet as address,
    cast(a.first_tx as varchar) as first_tx,
    cast(a.last_tx as varchar) as last_tx,
    date_diff('day', a.first_tx, now()) as age_days
from activity a
join balances b on b.wallet = a.wallet
join recent_active r on r.wallet = a.wallet
order by a.last_tx desc
limit {sample_size_val}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
