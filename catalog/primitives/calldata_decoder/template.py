# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
FUNCTION_NAME = "{{function_name}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo", "fantom", "gnosis", "linea", "scroll", "blast", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ALLOWED_LIMITS = {"10", "25", "50", "100"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

# A bare function name (no argument types) is ambiguous without the contract's
# ABI, since the selector depends on the full signature. These cover common,
# unambiguous single-overload cases as a convenience.
KNOWN_SELECTORS = {
    "transfer": "a9059cbb",
    "approve": "095ea7b3",
    "transferfrom": "23b872dd",
    "mint": "40c10f19",
    "burn": "42966c68",
    "deposit": "d0e30db0",
    "withdraw": "2e1a7d4d",
}

_KECCAK_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]
_KECCAK_ROT = [
    [0, 1, 62, 28, 27],
    [36, 44, 6, 55, 20],
    [3, 10, 43, 25, 39],
    [41, 45, 15, 21, 8],
    [18, 2, 61, 56, 14],
]
_KECCAK_MASK = (1 << 64) - 1


def _keccak_rol(x, s):
    s %= 64
    return x if s == 0 else ((x << s) | (x >> (64 - s))) & _KECCAK_MASK


def _keccak_f(state):
    for rc in _KECCAK_RC:
        C = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20] for x in range(5)]
        D = [C[(x - 1) % 5] ^ _keccak_rol(C[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] ^= D[x]

        B = [0] * 25
        for x in range(5):
            for y in range(5):
                B[y + 5 * ((2 * x + 3 * y) % 5)] = _keccak_rol(state[x + 5 * y], _KECCAK_ROT[y][x])

        for y in range(5):
            row = [B[x + 5 * y] for x in range(5)]
            for x in range(5):
                state[x + 5 * y] = (row[x] ^ ((~row[(x + 1) % 5]) & row[(x + 2) % 5])) & _KECCAK_MASK

        state[0] ^= rc
    return state


def keccak256(data: bytes) -> bytes:
    rate = 136  # 1088-bit rate for 256-bit output
    padlen = rate - (len(data) % rate)
    padded = data + (bytes([0x81]) if padlen == 1 else bytes([0x01]) + bytes(padlen - 2) + bytes([0x80]))

    state = [0] * 25
    for offset in range(0, len(padded), rate):
        block = padded[offset:offset + rate]
        for i in range(17):
            state[i] ^= int.from_bytes(block[i * 8:i * 8 + 8], "little")
        _keccak_f(state)

    return b"".join(state[i].to_bytes(8, "little") for i in range(4))


def function_selector(signature: str) -> str:
    """4-byte selector (hex, no 0x) for a full Solidity function signature, e.g. 'transfer(address,uint256)'."""
    return keccak256(signature.encode()).hex()[:8]


if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT not in ALLOWED_LIMITS:
    raise ValueError(f"Unsupported limit: {LIMIT!r}")

function_name_clean = FUNCTION_NAME.strip()
if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\(.*\)$", function_name_clean):
    # Full signature supplied (e.g. "transfer(address,uint256)") — hash it directly.
    selector = function_selector(function_name_clean)
else:
    selector = KNOWN_SELECTORS.get(function_name_clean.lower())
    if selector is None:
        raise ValueError(
            f"Cannot resolve a 4-byte selector for {FUNCTION_NAME!r} without its full signature. "
            f"Pass the full signature (e.g. 'transfer(address,uint256)') or use one of: {sorted(KNOWN_SELECTORS)}"
        )

time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS}' DAY"

sql = f"""
select
    block_time,
    block_number,
    hash as tx_hash,
    "from" as caller,
    "to" as contract_address,
    value,
    gas_used,
    data as calldata
from {CHAIN}.transactions
where "to" = from_hex('{CONTRACT_ADDRESS[2:].lower()}')
  and substr(data, 1, 4) = from_hex('{selector}')
  {time_where}
order by block_time desc
limit {LIMIT}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
