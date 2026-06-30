"""Run: uv run python seed.py"""

import asyncio

from config import load_config
from db.init import close_db, init_db
from db.models import Brand, Phone
from train_test_data import brands, phones


async def main() -> None:
    config = load_config()
    await init_db(config.database_url)

    # Brands
    for b in brands:
        await Brand.get_or_create(name=b["name"])
    print(f"Seeded {len(brands)} brands.")

    # Phones — each entry is a distinct row (same model, different color = separate row)
    count = 0
    for p in phones:
        await Phone.get_or_create(
            name=p["name"],
            brand_id=p["brand"],
            price=p["price"],
            buy_link=p["link"],
            defaults={
                "rom_options": p.get("rom_options", []),
                "ram_options": p.get("ram_options", []),
                "colors": p.get("colors", []),
            },
        )
        count += 1
    print(f"Seeded {count} phones.")

    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
