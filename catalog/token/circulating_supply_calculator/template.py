# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
MINTS_CSV = '''{{mints_csv}}'''
CUTOFF_TIME = "{{cutoff_time}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(CUTOFF_TIME):
    raise ValueError(f"Invalid cutoff_time: {CUTOFF_TIME!r}")

# "mint" is SPL-token (Solana) terminology for a token's contract address; on
# EVM chains the equivalent identifier is the ERC-20 contract address.
mints = [a.strip() for a in MINTS_CSV.split(",") if a.strip()]
if not mints:
    raise ValueError("mints_csv must contain at least one contract address")
for a in mints:
    if not ADDRESS_RE.match(a):
        raise ValueError(f"Invalid contract address in mints_csv: {a!r}")

mint_hex_list = [a[2:].lower() for a in mints]
values_clause = ", ".join(f"(from_hex('{h}'))" for h in mint_hex_list)

sql = f"""
with target_mints (contract_address) as (
    values {values_clause}
),
mints_agg as (
    select t.contract_address, sum(tr.amount) as total_minted
    from target_mints t
    left join tokens.transfers tr
      on tr.blockchain = '{CHAIN}'
     and tr.token_standard = 'erc20'
     and tr.contract_address = t.contract_address
     and tr."from" = from_hex('0000000000000000000000000000000000000000')
     and tr.block_time <= timestamp '{CUTOFF_TIME}'
    group by t.contract_address
),
burns_agg as (
    select t.contract_address, sum(tr.amount) as total_burned
    from target_mints t
    left join tokens.transfers tr
      on tr.blockchain = '{CHAIN}'
     and tr.token_standard = 'erc20'
     and tr.contract_address = t.contract_address
     and tr."to" in (from_hex('0000000000000000000000000000000000000000'), from_hex('000000000000000000000000000000000000dead'))
     and tr.block_time <= timestamp '{CUTOFF_TIME}'
    group by t.contract_address
)
select
    to_hex(m.contract_address) as mint,
    coalesce(m.total_minted, 0) - coalesce(b.total_burned, 0) as circulating_supply
from mints_agg m
join burns_agg b on b.contract_address = m.contract_address
order by circulating_supply desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
