# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

# Canonical native-issuance deployments only (not bridged wrapped copies),
# since only the issuer's own contract exposes real blacklist events.
USDC_ADDRESSES = {
    "ethereum": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "base": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
    "optimism": "0x0b2c639c533813f4aa9d7837caf62653d097ff85",
    "arbitrum": "0xaf88d065e77c8cc2239327c5edb3a432268e5831",
    "polygon": "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",
    "avalanche": "0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e",
    "celo": "0xceba9300f2b948710d2653dd7b07f33a8b32118c",
}
USDT_ADDRESSES = {
    "ethereum": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "polygon": "0xc2132d05d31c914a87c6611c10748aeb04b58e8f",
    "bsc": "0x55d398326f99059ff775485246999027b3197955",
    "avalanche": "0x9702230a8ea53601f5cd2dc00fdbc13d4df4a8c7",
    "arbitrum": "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9",
    "optimism": "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

contract_lower = CONTRACT_ADDRESS.lower()

# USDC's FiatTokenV2 emits `Blacklisted(address indexed _account)`; the
# older Tether USDT contract emits `AddedBlackList(address _user)`. Both are
# real, verifiable on-chain events — assumes Dune Spellbook's standard
# per-contract decoded-event table naming (`<project>_<chain>.<Contract>_evt_<Event>`).
if USDC_ADDRESSES.get(CHAIN) == contract_lower:
    sql = f"""
    select evt_block_time as block_time, _account as address
    from usdc_{CHAIN}.FiatTokenV2_2_evt_Blacklisted
    order by evt_block_time
    """
elif USDT_ADDRESSES.get(CHAIN) == contract_lower:
    sql = f"""
    select evt_block_time as block_time, _user as address
    from tether_{CHAIN}.TetherToken_evt_AddedBlackList
    order by evt_block_time
    """
else:
    raise ValueError(
        f"contract_address {CONTRACT_ADDRESS!r} is not a known native USDC/USDT deployment on chain {CHAIN!r}"
    )

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
