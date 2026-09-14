# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN_ADDRESS1 = "{{token_address1}}"
TOKEN_ADDRESS2 = "{{token_address2}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN_ADDRESS1):
    raise ValueError(f"Invalid token_address1: {TOKEN_ADDRESS1!r}")
if not ADDRESS_RE.match(TOKEN_ADDRESS2):
    raise ValueError(f"Invalid token_address2: {TOKEN_ADDRESS2!r}")

token1_hex = TOKEN_ADDRESS1[2:].lower()
token2_hex = TOKEN_ADDRESS2[2:].lower()

# Both tokens are assumed to live on the same chain — holder overlap across
# two different chains would require bridging identity assumptions this
# catalog doesn't make.
sql = f"""
with movements1 as (
    select "to" as wallet, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{token1_hex}')
    union all
    select "from" as wallet, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{token1_hex}')
),
movements2 as (
    select "to" as wallet, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{token2_hex}')
    union all
    select "from" as wallet, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}' and token_standard = 'erc20' and contract_address = from_hex('{token2_hex}')
),
holders1 as (
    select wallet from movements1 group by wallet having sum(amt) > 0
),
holders2 as (
    select wallet from movements2 group by wallet having sum(amt) > 0
),
overlap as (
    select h1.wallet from holders1 h1 inner join holders2 h2 on h1.wallet = h2.wallet
)
select
    (select count(*) from overlap) as overlap_count,
    (select count(*) from holders1) as holders_token1,
    (select count(*) from holders2) as holders_token2,
    100.0 * (select count(*) from overlap) / nullif((select count(*) from holders1), 0) as overlap_pct
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
