
def paggination(page: int = 1, count: int = 10) -> dict[str, int]:
    return {
        "offset": (page - 1) * count,
        "limit": count
    }
