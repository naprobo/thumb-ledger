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
    "category.dining": ["item.restaurant", "item.cafe", "item.takeout", "item.fastFood", "item.bar"],
    "category.daily": ["item.tissues", "item.detergent", "item.shampoo", "item.toothpaste", "item.trashBags"],
    "category.clothing": ["item.tshirt", "item.pants", "item.coat", "item.socks", "item.shoes"],
    "category.housing": ["item.rent", "item.mortgage", "item.propertyFee", "item.maintenanceFund", "item.utilities"],
    "category.utilities": ["item.electricity", "item.water", "item.gas", "item.heating", "item.internet"],
    "category.communication": ["item.mobilePhone", "item.broadband", "item.simCard", "item.cloudStorage", "item.postage"],
    "category.transport": ["item.train", "item.bus", "item.taxi", "item.rideShare", "item.airfare"],
    "category.vehicle": ["item.gasoline", "item.evCharge", "item.parking", "item.toll", "item.carInspection", "item.carMaintenance"],
    "category.medical": ["item.medicine", "item.clinic", "item.dental", "item.eyeDrops", "item.checkup"],
    "category.insurance": ["item.healthInsurance", "item.lifeInsurance", "item.homeInsurance", "item.travelInsurance", "item.pension"],
    "category.education": ["item.tuition", "item.tutoring", "item.textbook", "item.onlineCourse", "item.examFee"],
    "category.childcare": ["item.diapers", "item.formula", "item.childcare", "item.babySupplies", "item.childrenActivity"],
    "category.pets": ["item.petFood", "item.petSupplies", "item.vet", "item.petGrooming", "item.petInsurance"],
    "category.entertainment": ["item.movie", "item.game", "item.book", "item.toy", "item.ticket"],
    "category.travel": ["item.hotel", "item.sightseeing", "item.visa", "item.luggage", "item.travelTransport"],
    "category.digital": ["item.phone", "item.computer", "item.appliance", "item.accessory", "item.deviceRepair"],
    "category.subscriptions": ["item.videoStreaming", "item.musicStreaming", "item.appSubscription", "item.softwareSubscription", "item.membership"],
    "category.social": ["item.gift", "item.redEnvelope", "item.weddingGift", "item.treat", "item.donation"],
    "category.beauty": ["item.haircut", "item.skincare", "item.cosmetics", "item.nailSalon", "item.fitness"],
    "category.taxes": ["item.tax", "item.bankFee", "item.adminFee", "item.certificateFee", "item.lateFee"],
    "category.other": ["item.misc", "item.fee", "item.repair", "item.lostItem", "item.emergency"],
}

DEFAULT_CATEGORIES = list(DEFAULT_ITEM_SUGGESTIONS.keys())
