"""Shared enums used across the application."""

from __future__ import annotations

import enum


class SearchCategory(str, enum.Enum):
    FOOD = "food"
    PRODUCT = "product"
    RIDE = "ride"
    HOTEL = "hotel"


class Platform(str, enum.Enum):
    # Food
    UBER_EATS = "uber_eats"
    DOORDASH = "doordash"
    GRUBHUB = "grubhub"
    POSTMATES = "postmates"
    # E-Commerce
    AMAZON = "amazon"
    EBAY = "ebay"
    WALMART = "walmart"
    TARGET = "target"
    BESTBUY = "bestbuy"
    # Rides
    UBER = "uber"
    LYFT = "lyft"
    TAXI = "taxi"
    # Hotels
    BOOKING = "booking"
    EXPEDIA = "expedia"
    AIRBNB = "airbnb"
    HOTELS_COM = "hotels_com"
    VRBO = "vrbo"


class DealType(str, enum.Enum):
    PROMO_CODE = "promo_code"
    CASHBACK = "cashback"
    CREDIT_CARD = "credit_card"
    SEASONAL = "seasonal"
    FLASH_SALE = "flash_sale"
    LOYALTY = "loyalty"


class SearchStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
