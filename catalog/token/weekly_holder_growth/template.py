# Sandworm Power Toolbox — {{__tool_name}}
import re
from datetime import datetime

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if DATE_FROM:
    try:
        datetime.strptime(DATE_FROM, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
date_where = f"and block_time >= date '{DATE_FROM}'" if DATE_FROM else ""

sql = f"""
with movements as (
    select date_trunc('week', block_time) as week, "to" as wallet, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      {date_where}
    union all
    select date_trunc('week', block_time) as week, "from" as wallet, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      {date_where}
),
weekly_net as (
    select week, wallet, sum(amt) as net_amt
    from movements
    group by week, wallet
),
running as (
    select
        week,
        wallet,
        sum(net_amt) over (partition by wallet order by week rows between unbounded preceding and current row) as cum_balance
    from weekly_net
),
all_weeks as (
    select distinct week from weekly_net
),
-- Forward-fills each wallet's most recently known cumulative balance into
-- every later week, so a wallet that goes quiet still counts as a holder
-- until it actually sells out.
wallet_weeks as (
    select week, wallet, cum_balance
    from (
        select
            w.week,
            r.wallet,
            r.cum_balance,
            row_number() over (partition by w.week, r.wallet order by r.week desc) as rn
        from all_weeks w
        join running r on r.week <= w.week
    ) ranked
    where rn = 1
),
holders_per_week as (
    select week, count(distinct wallet) as holder_count
    from wallet_weeks
    where cum_balance > 0
    group by week
)
select
    week,
    holder_count,
    100.0 * (holder_count - lag(holder_count) over (order by week)) / nullif(lag(holder_count) over (order by week), 0) as growth_rate
from holders_per_week
order by week
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
