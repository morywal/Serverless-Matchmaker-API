"""Map an MMR value to a Valorant-style rank tier."""

# (minimum MMR, tier name), ordered from highest to lowest.
RANK_THRESHOLDS = (
    (3200, "Radiant"),
    (2800, "Immortal"),
    (2400, "Ascendant"),
    (2000, "Diamond"),
    (1600, "Platinum"),
    (1200, "Gold"),
    (800, "Silver"),
    (400, "Bronze"),
    (0, "Iron"),
)


def get_rank_tier(mmr: int) -> str:
    """Return the rank tier for a non-negative MMR value."""
    if mmr < 0:
        raise ValueError("mmr must be >= 0")
    for minimum, tier in RANK_THRESHOLDS:
        if mmr >= minimum:
            return tier
    return "Iron"  # unreachable, kept for safety
