# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
MIN_PERCENT = "{{min_percent}}".strip() or "1"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    min_percent = float(MIN_PERCENT)
except ValueError:
    raise ValueError(f"Invalid min_percent: {MIN_PERCENT!r}")
if min_percent <= 0:
    raise ValueError(f"min_percent must be > 0: {MIN_PERCENT!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# Total minted supply is derived from mint transfers (from the zero address),
# since a generic total_supply column isn't available across all ERC20s.
sql = f"""
with minted as (
    select sum(amount) as total_minted
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "from" = from_hex('0000000000000000000000000000000000000000')
),
transfers as (
    select
        t."to" as wallet,
        t.tx_hash,
        t.amount
    from tokens.transfers t
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{token_hex}')
      and t."from" != from_hex('0000000000000000000000000000000000000000')
)
select
    t.wallet,
    100.0 * t.amount / nullif(m.total_minted, 0) as percent_supply,
    t.tx_hash as tx_id,
    (100.0 * t.amount / nullif(m.total_minted, 0)) >= {min_percent} as is_significant
from transfers t
cross join minted m
where (100.0 * t.amount / nullif(m.total_minted, 0)) >= {min_percent}
order by percent_supply desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
