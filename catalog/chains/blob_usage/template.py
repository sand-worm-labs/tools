# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

# Blob (EIP-4844) fields only exist on ethereum.transactions — L2s post their
# blobs *to* L1, they don't originate them, so this tool is L1-only.
ALLOWED_CHAINS = {"ethereum"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS}' DAY"
limit_clause = f"limit {LIMIT}" if LIMIT else ""

# Mapping the L1 "to" address of a blob tx to a specific L2 name requires a
# curated, regularly-refreshed batcher-inbox address list this catalog does
# not maintain yet, so submitters are reported by raw address (rank by usage)
# rather than a guessed chain label.
sql = f"""
with blob_txs as (
    select
        block_time,
        "to" as batch_inbox_address,
        blob_gas_used,
        blob_gas_price,
        cardinality(blob_versioned_hashes) as blob_count
    from {CHAIN}.transactions
    where blob_gas_used > 0
      {time_where}
)
select
    date_trunc('day', block_time) as day,
    batch_inbox_address,
    count(*) as blob_tx_count,
    sum(blob_count) as total_blobs,
    sum(blob_gas_used * blob_gas_price) / 1e18 as total_blob_fees_eth,
    avg(blob_gas_price) / 1e9 as avg_blob_gas_price_gwei
from blob_txs
group by 1, 2
order by 1 desc, total_blobs desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="day", y="total_blobs", color="batch_inbox_address")
fig.show()

{{__df_name}}
