# Sandworm Power Toolbox — {{__tool_name}}
# "ETH transfers" reinterpreted generically as native-gas-token transfers on
# whichever EVM chain is selected (native value moved via CALL traces), since
# this catalog is EVM-only and chain-agnostic.
from datetime import datetime

CHAIN = "{{chain}}"
MIN_USD = "{{min_usd}}".strip()
DATE_FROM = "{{date_from}}".strip()
TOP_N = "{{top_n}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
# Raw per-chain Spellbook schema names differ from the `blockchain` column
# values used in decoded tables (e.g. bsc's raw schema is "bnb").
RAW_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}
# Sentinel contract_address Dune's prices.usd uses for a chain's native gas token.
NATIVE_ADDRESS_HEX = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
try:
    min_usd_val = float(MIN_USD)
except ValueError:
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")
if min_usd_val < 0:
    raise ValueError(f"min_usd must be >= 0: {MIN_USD!r}")
if not TOP_N:
    top_n_val = 100
elif TOP_N.isdigit() and int(TOP_N) > 0:
    top_n_val = int(TOP_N)
else:
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

# date_from is declared as a `date` input but this tool's own default ('7')
# looks like a lookback-day count; accept either an ISO date or a bare
# integer number of days so both interpretations work.
if not DATE_FROM:
    date_where = ""
elif DATE_FROM.isdigit():
    date_where = f"and block_time >= now() - interval '{DATE_FROM}' day"
else:
    try:
        datetime.strptime(DATE_FROM, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
    date_where = f"and block_time >= date '{DATE_FROM}'"

raw_schema = RAW_SCHEMA[CHAIN]

sql = f"""
with native_transfers as (
    select block_time, "to" as to_address, value / 1e18 as amount_native
    from {raw_schema}.traces
    where call_type = 'call'
      and value > 0
      and success = true
      {date_where}
),
priced as (
    select
        n.block_time,
        n.to_address,
        n.amount_native,
        n.amount_native * coalesce(p.price, 0) as amount_usd
    from native_transfers n
    left join prices.usd p
        on p.blockchain = '{CHAIN}'
        and p.contract_address = from_hex('{NATIVE_ADDRESS_HEX}')
        and p.minute = date_trunc('minute', n.block_time)
),
whale_transfers as (
    select
        date_trunc('day', block_time) as day,
        to_address,
        amount_native
    from priced
    where amount_usd >= {min_usd_val}
)
select
    day,
    '0x' || lower(to_hex(to_address)) as to_address,
    sum(amount_native) as total_eth,
    count(*) as tx_count
from whale_transfers
group by day, to_address
order by day desc, total_eth desc
limit {top_n_val}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
