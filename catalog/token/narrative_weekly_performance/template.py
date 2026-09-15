# Sandworm Power Toolbox — {{__tool_name}}
# "narrative" maps to a small curated basket of well-known token symbols per
# theme, since there is no canonical on-chain "narrative" taxonomy in Spellbook.
CHAIN = "{{chain}}"
NARRATIVE = "{{narrative}}".strip().lower()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
NARRATIVE_BASKETS = {
    "real_yield": ["GMX", "GNS", "SNX", "DYDX"],
    "l2": ["ARB", "OP", "MATIC", "METIS"],
    "ai": ["FET", "AGIX", "RNDR", "TAO"],
    "meme": ["PEPE", "SHIB", "FLOKI", "DOGE"],
    "defi": ["UNI", "AAVE", "CRV", "MKR"],
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if NARRATIVE not in NARRATIVE_BASKETS:
    raise ValueError(f"Unsupported narrative: {NARRATIVE!r}. Choose from: {sorted(NARRATIVE_BASKETS)}")

symbol_list = ", ".join(f"'{s}'" for s in NARRATIVE_BASKETS[NARRATIVE])

sql = f"""
with weekly_prices as (
    select
        symbol,
        date_trunc('week', minute) as week,
        price,
        row_number() over (partition by symbol, date_trunc('week', minute) order by minute asc) as rn_first,
        row_number() over (partition by symbol, date_trunc('week', minute) order by minute desc) as rn_last
    from prices.usd
    where blockchain = '{CHAIN}'
      and symbol in ({symbol_list})
),
agg as (
    select
        symbol,
        week,
        max(case when rn_first = 1 then price end) as price_initial,
        max(case when rn_last = 1 then price end) as price_end
    from weekly_prices
    group by symbol, week
)
select
    week,
    symbol,
    price_initial,
    price_end,
    (price_end - price_initial) / nullif(price_initial, 0) as return_pct
from agg
order by week, symbol
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
