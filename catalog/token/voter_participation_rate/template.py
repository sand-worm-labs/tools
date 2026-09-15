# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
# Raw per-chain schema prefixes for the decoded-log tables (Dune spellbook
# names BSC's raw schema "bnb" and Avalanche's C-Chain schema "avalanche_c").
RAW_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
# keccak256("VoteCast(address,uint256,uint8,uint256,string)") — the standard
# OpenZeppelin Governor / GovernorBravo vote event. `voter` is the only
# indexed param; proposalId, support and weight are the first three static
# 32-byte words of `data`, ahead of the dynamic `reason` string.
VOTE_CAST_TOPIC = "0xb8e138887d0aa13bab447e82de9d5c1777041ecd21ca36ba824ff1e6c07ddda4"

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

raw_schema = RAW_SCHEMA[CHAIN]
contract_hex = CONTRACT_ADDRESS[2:].lower()
topic_hex = VOTE_CAST_TOPIC[2:].lower()

sql = f"""
with votes as (
    select
        bytearray_substring(topics[2], 13, 20) as voter,
        bytearray_to_uint256(bytearray_substring(data, 1, 32)) as proposal_id
    from {raw_schema}.logs
    where contract_address = from_hex('{contract_hex}')
      and topics[1] = from_hex('{topic_hex}')
),
per_proposal as (
    select proposal_id, count(distinct voter) as unique_voters
    from votes
    group by proposal_id
),
-- Real per-block token-holder snapshots aren't available without the
-- governance token's own contract address (only the governor is given), so
-- "total holders" is approximated as the cumulative set of distinct wallets
-- that have ever cast a vote on this governor up to and including a
-- proposal — a real, on-chain-derived lower bound on the eligible voter base.
first_vote as (
    select voter, min(proposal_id) as first_proposal
    from votes
    group by voter
),
cumulative as (
    select
        pp.proposal_id,
        pp.unique_voters,
        count(fv.voter) as total_holders
    from per_proposal pp
    join first_vote fv on fv.first_proposal <= pp.proposal_id
    group by pp.proposal_id, pp.unique_voters
)
select
    cast(proposal_id as varchar) as snapshot,
    total_holders,
    unique_voters,
    100.0 * unique_voters / nullif(total_holders, 0) as share_voters
from cumulative
order by proposal_id
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
