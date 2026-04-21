import re
import random
import string
from typing import Any, Optional
import socket
from datetime import datetime
from reflex.vars import NumberVar, var_operation, var_operation_return
from zoneinfo import ZoneInfo


@var_operation
def two_decimal_points(value: NumberVar):
    """This function will return the value with two decimal points."""
    return var_operation_return(
        js_expression=f"({value}.toFixed(2))",
        var_type=str,
    )


def safe_float_convert(s: str) -> Optional[float]:
    try:
        return float(s)
    except ValueError:
        return None
    except TypeError:
        return None


def value_or(x: Optional[Any], default: Any) -> Any:
    return x if not x is None else default


_alphabet = string.ascii_lowercase + string.digits


def short_uid(k=8):
    return "".join(random.choices(_alphabet, k=8))


def lower_non_alpha_num(s: str) -> str:
    return re.sub(r"\W+", "", s).lower()


def check_internet_connection():
    try:
        socket.create_connection(("www.google.com", 443), timeout=3)
    except OSError:
        print(f"No internet connection - {get_madrid_datetime_now()}", flush=True)
        raise


def get_model_string_type_columns(model):
    string_type_columns = []

    for col in model.__table__.columns:
        if str(col.type) != "VARCHAR":
            continue

        string_type_columns.append(col.name)

    return string_type_columns


def sanitise_record_strings(string_type_columns, record):
    for key in record:
        if not key in string_type_columns:
            continue

        record[key] = str(record[key])
    return record


def generate_receiver_from_names(first_name, last_name):
    return f"{first_name.upper().strip()} {last_name.upper().strip()}"


def get_madrid_datetime_now():
    return datetime.now(ZoneInfo("Europe/Madrid"))


def generate_line_item(name: str, unit_amount: int, quantity: int):
    return {
        "price_data": {
            "currency": "eur",
            "product_data": {"name": name},
            "unit_amount": unit_amount,
        },
        "quantity": quantity,
    }
