"""
Supported currency codes for user-selectable bookkeeping currencies.
"""

SUPPORTED_CURRENCY_CODES = {
    "JPY",
    "CNY",
    "USD",
    "EUR",
    "GBP",
    "KRW",
    "TWD",
    "HKD",
    "SGD",
    "AUD",
    "CAD",
    "CHF",
    "NZD",
    "THB",
    "VND",
    "IDR",
    "MYR",
    "PHP",
    "INR",
    "BRL",
    "MXN",
    "ZAR",
    "SEK",
    "NOK",
    "DKK",
    "PLN",
    "CZK",
    "HUF",
    "TRY",
    "AED",
    "SAR",
    "ILS",
}


def validate_supported_currency(currency_code: str | None) -> str | None:
    if currency_code is None:
        return None
    if currency_code not in SUPPORTED_CURRENCY_CODES:
        raise ValueError("unsupported currency code")
    return currency_code
