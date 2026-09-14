# Sandworm Power Toolbox — {{__tool_name}}
# Original name implied a pump.fun-style Solana launchpad dev-wallet pattern;
# reinterpreted for EVM as wallets repeatedly calling an ERC20 factory contract
# to deploy new tokens (e.g. a Uniswap-style token-launch factory).
import re

CHAIN = "{{chain}}"
FACTORY_ADDRESS = "{{factory_address}}"
TOP_N = "{{top_n}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
CHAIN_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(FACTORY_ADDRESS):
    raise ValueError(f"Invalid factory_address: {FACTORY_ADDRESS!r}")
if not TOP_N.isdigit() or int(TOP_N) <= 0:
    raise ValueError(f"Invalid top_n: {TOP_N!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]
factory_hex = FACTORY_ADDRESS[2:].lower()

sql = f"""
select
    "from" as dev_wallet,
    count(*) as token_count,
    count(*) * 1.0 / {LOOKBACK_DAYS} as bot_score
from {schema}.transactions
where "to" = from_hex('{factory_hex}')
  and success = true
  and block_time >= now() - interval '{LOOKBACK_DAYS}' day
group by 1
order by token_count desc
limit {TOP_N}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
