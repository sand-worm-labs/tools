# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WRAPPED_CONTRACT = "{{wrapped_contract}}"
UNDERLYING_CONTRACT = "{{underlying_contract}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WRAPPED_CONTRACT):
    raise ValueError(f"Invalid wrapped_contract: {WRAPPED_CONTRACT!r}")
if not ADDRESS_RE.match(UNDERLYING_CONTRACT):
    raise ValueError(f"Invalid underlying_contract: {UNDERLYING_CONTRACT!r}")

wrapped_hex = WRAPPED_CONTRACT[2:].lower()
underlying_hex = UNDERLYING_CONTRACT[2:].lower()

# Assumes a 1:1 wrap/unwrap pattern per tx (typical of deposit/withdraw-style
# wrapping); a tx with multiple transfer events of either token will fan out
# across the join below.
sql = f"""
with wrapped_transfers as (
    select
        t.tx_hash,
        t.block_time,
        t.amount / power(10, coalesce(e.decimals, 18)) as wrapped_amount
    from tokens.transfers t
    left join tokens.erc20 e
        on e.blockchain = '{CHAIN}' and e.contract_address = t.contract_address
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{wrapped_hex}')
),
underlying_transfers as (
    select
        t.tx_hash,
        t.amount / power(10, coalesce(e.decimals, 18)) as underlying_amount
    from tokens.transfers t
    left join tokens.erc20 e
        on e.blockchain = '{CHAIN}' and e.contract_address = t.contract_address
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{underlying_hex}')
)
select
    w.block_time as time,
    u.underlying_amount / nullif(w.wrapped_amount, 0) as ratio,
    w.wrapped_amount,
    u.underlying_amount
from wrapped_transfers w
join underlying_transfers u on u.tx_hash = w.tx_hash
order by w.block_time desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
