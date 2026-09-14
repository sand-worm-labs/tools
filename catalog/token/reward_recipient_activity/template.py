# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
REWARD_FROM = "{{reward_from}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DATE_FROM = "{{date_from}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(REWARD_FROM):
    raise ValueError(f"Invalid reward_from: {REWARD_FROM!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

reward_from_hex = REWARD_FROM[2:].lower()
token_hex = CONTRACT_ADDRESS[2:].lower()

# "First activity" is the recipient's first outbound transfer of this token
# after receiving a reward; total_out sums everything they've sent out since.
sql = f"""
with reward_recipients as (
    select "to" as recipient, min(block_time) as first_reward_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "from" = from_hex('{reward_from_hex}')
      and block_time >= date('{DATE_FROM}')
    group by 1
),
outbound as (
    select
        t."from" as recipient,
        min(t.block_time) as first_outbound_time,
        sum(t.amount) as total_out
    from tokens.transfers t
    join reward_recipients r on r.recipient = t."from"
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{token_hex}')
      and t.block_time > r.first_reward_time
    group by 1
)
select
    r.recipient,
    coalesce(o.first_outbound_time, r.first_reward_time) as first_activity,
    coalesce(o.total_out, 0) as total_out
from reward_recipients r
left join outbound o on o.recipient = r.recipient
order by first_activity
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
