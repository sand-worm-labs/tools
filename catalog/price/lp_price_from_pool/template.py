# Sandworm Power Toolbox — {{__tool_name}}
import re

POOL_ADDRESS = "{{pool_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if not ADDRESS_RE.match(POOL_ADDRESS):
    raise ValueError(f"Invalid pool_address: {POOL_ADDRESS!r}")
if not (LOOKBACK_DAYS.isdigit() and int(LOOKBACK_DAYS) > 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

# Approximates pool price from executed trade prices against this pool contract,
# since a generic per-DEX reserves table isn't available across all projects.
sql = f"""
select
    date_trunc('day', block_time) as day,
    avg(amount_usd / nullif(token_bought_amount, 0)) as price
from dex.trades
where project_contract_address = from_hex('{POOL_ADDRESS[2:].lower()}')
  and block_time >= now() - interval '{LOOKBACK_DAYS}' day
  and token_bought_amount > 0
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y=['price'])
fig.show()

{{__df_name}}
