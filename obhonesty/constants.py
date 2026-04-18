from enum import StrEnum

true_values = ["yes", "true", "1", "y"]
default_button_text_size = "4"
default_heading_size = "7"
default_text_size = "4"
default_button_size = "4"
ERROR_MESSAGE_COLOUR = "var(--red-11)"
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
SYSTEM_PROVIDER_HANDLING_FEE = 0.0325


class Diet(StrEnum):
    VEGAN = "Vegan"
    VEGETARIAN = "Vegetarian"
    MEAT = "Meat"


class BreakfastMenuItem(StrEnum):
    VEGAN = "Vegan"
    SMALL = "Small"
    CONTINENTAL = "Continental"
    FULL_ENGLISH = "Full English"
    VEGETARIAN = "Vegetarian"
    PACKED_LUNCH_VEGAN = "Packed Lunch (Vegan)"
    PACKED_LUNCH_VEGETARIAN = "Packed Lunch (Vegetarian)"
    PACKED_LUNCH_MEAT = "Packed Lunch (Meat)"


class TaxCategory(StrEnum):
    NON_ALCOHOLIC = "Food and beverage non-alcoholic"
    ALCOHOLIC = "Beverage with alcohol"
    FITNESS = "Fitness"
    MISC = "Miscellaneous"
    ACCOMMODATION = "Accommodation"
