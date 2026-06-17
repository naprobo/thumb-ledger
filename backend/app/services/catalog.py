"""
默认分类与商品建议 catalog。
"""

DEFAULT_SUBJECTS = [
    "subject.self",
    "subject.dad",
    "subject.mom",
    "subject.child",
    "subject.grandpa",
    "subject.grandma",
    "subject.husband",
    "subject.wife",
    "subject.brother",
    "subject.sister",
]

DEFAULT_ITEM_SUGGESTIONS: dict[str, list[str]] = {
    "category.food": ["item.rice", "item.eggs", "item.milk", "item.vegetables", "item.fruit"],
    "category.clothing": ["item.tshirt", "item.pants", "item.coat", "item.socks", "item.shoes"],
    "category.daily": ["item.tissues", "item.detergent", "item.shampoo", "item.toothpaste", "item.trashBags"],
    "category.housing": ["item.rent", "item.mortgage", "item.propertyFee", "item.maintenanceFund", "item.utilities"],
    "category.transport": ["item.train", "item.bus", "item.taxi", "item.gasoline", "item.parking"],
    "category.entertainment": ["item.movie", "item.game", "item.book", "item.toy", "item.ticket"],
    "category.medical": ["item.medicine", "item.clinic", "item.dental", "item.eyeDrops", "item.checkup"],
    "category.other": ["item.gift", "item.fee", "item.repair", "item.subscription", "item.misc"],
}

DEFAULT_CATEGORIES = list(DEFAULT_ITEM_SUGGESTIONS.keys())
