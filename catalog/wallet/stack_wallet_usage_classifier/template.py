# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
TOP_N = "{{top_n}}"
LOOKBACK_DAYS = "{{lookback_days}}"

CHAIN_SCHEMA = {
    "ethereum": "ethereum",
    "base": "base",
    "optimism": "optimism",
    "arbitrum": "arbitrum",
    "polygon": "polygon",
    "bsc": "bnb",
    "avalanche": "avalanche_c",
    "celo": "celo",
}
ALLOWED_CHAINS = set(CHAIN_SCHEMA)

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOP_N.isdigit() or int(TOP_N) <= 0:
    raise ValueError(f"Invalid top_n: {TOP_N!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]

# No confirmed "Stack" wallet product/table could be identified, so wallet
# creation is proxied by an address's first-ever outbound transaction, and
# "liquidation-type events" are proxied by large ($1k+) post-creation token
# outflows, using only standard chain-generic tables.
sql = f"""
with wallet_first_seen as (
    select "from" as wallet, min(block_time) as creation_time
    from {schema}.transactions
    where success
    group by 1
    having min(block_time) >= now() - interval '{LOOKBACK_DAYS}' day
),
outflows as (
    select
        t."from" as wallet,
        t.symbol,
        t.amount_usd
    from tokens.transfers t
    join wallet_first_seen w on w.wallet = t."from"
    where t.blockchain = '{CHAIN}'
      and t.amount_usd >= 1000
      and t.block_time > w.creation_time
),
scored as (
    select
        wallet,
        count(*) as activity_score,
        array_join(array_agg(distinct symbol), ',') as signals
    from outflows
    group by 1
)
select
    to_hex(s.wallet) as wallet,
    w.creation_time,
    s.activity_score,
    s.signals
from scored s
join wallet_first_seen w on w.wallet = s.wallet
order by s.activity_score desc
limit {TOP_N}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
