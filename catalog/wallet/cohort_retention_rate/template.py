# Sandworm Power Toolbox — {{__tool_name}}
import json
import re

CHAIN = "{{chain}}"
DATE_RANGE_1 = json.loads("""{{date_range_1}}""")
DATE_RANGE_2 = json.loads("""{{date_range_2}}""")

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")

FROM_1, TO_1 = str(DATE_RANGE_1.get("from", "")), str(DATE_RANGE_1.get("to", ""))
FROM_2, TO_2 = str(DATE_RANGE_2.get("from", "")), str(DATE_RANGE_2.get("to", ""))
for label, value in (("date_range_1.from", FROM_1), ("date_range_1.to", TO_1), ("date_range_2.from", FROM_2), ("date_range_2.to", TO_2)):
    if not DATE_RE.match(value):
        raise ValueError(f"Invalid {label}: {value!r}")
if FROM_1 > TO_1:
    raise ValueError("date_range_1 'from' must not be after 'to'")
if FROM_2 > TO_2:
    raise ValueError("date_range_2 'from' must not be after 'to'")

sql = f"""
with cohort as (
    select distinct "from" as wallet
    from {CHAIN}.transactions
    where block_time >= date '{FROM_1}'
      and block_time < date '{TO_1}' + interval '1' day
),
retained as (
    select distinct t."from" as wallet
    from {CHAIN}.transactions t
    join cohort c on t."from" = c.wallet
    where t.block_time >= date '{FROM_2}'
      and t.block_time < date '{TO_2}' + interval '1' day
)
select
    (select count(*) from cohort) as initial_users,
    (select count(*) from retained) as retained_users,
    cast((select count(*) from retained) as double) / nullif((select count(*) from cohort), 0) as retention_rate
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
