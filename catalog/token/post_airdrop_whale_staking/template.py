# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
TOKEN_ADDRESS = "{{token_address}}"
CLAIM_CONTRACT = "{{claim_contract}}"
STAKING_CONTRACT = "{{staking_contract}}"
MIN_CLAIM = "{{min_claim}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN_ADDRESS):
    raise ValueError(f"Invalid token_address: {TOKEN_ADDRESS!r}")
if not ADDRESS_RE.match(CLAIM_CONTRACT):
    raise ValueError(f"Invalid claim_contract: {CLAIM_CONTRACT!r}")
if not ADDRESS_RE.match(STAKING_CONTRACT):
    raise ValueError(f"Invalid staking_contract: {STAKING_CONTRACT!r}")
if not MIN_CLAIM.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid min_claim: {MIN_CLAIM!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

token_hex = TOKEN_ADDRESS[2:].lower()
claim_hex = CLAIM_CONTRACT[2:].lower()
staking_hex = STAKING_CONTRACT[2:].lower()

# "Claim" = a transfer of the airdrop token out of the claim/distributor
# contract; "staking" = a subsequent transfer of that same token into the
# staking contract by the same wallet.
sql = f"""
with claims as (
    select "to" as whale, sum(amount) as claimed
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{token_hex}')
      and "from" = from_hex('{claim_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
    having sum(amount) >= {MIN_CLAIM}
),
staked as (
    select "from" as whale, sum(amount) as staked
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{token_hex}')
      and "to" = from_hex('{staking_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
)
select
    c.whale as whale_address,
    c.claimed,
    coalesce(s.staked, 0) as staked,
    coalesce(s.staked, 0) / nullif(c.claimed, 0) as accumulation_score
from claims c
left join staked s on s.whale = c.whale
order by c.claimed desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
