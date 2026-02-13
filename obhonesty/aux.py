
import re
import random
import string
from typing import Any, Optional
import socket 
from datetime import datetime

from reflex.vars import NumberVar, var_operation, var_operation_return

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
  return ''.join(random.choices(_alphabet, k=8))

def lower_non_alpha_num(s: str) -> str:
  return re.sub(r'\W+', '', s).lower()

def str_cmp(s: str, t: str) -> bool:
  return lower_non_alpha_num(s) == lower_non_alpha_num(t)

def check_internet_connection():
    try:
        socket.create_connection(("www.google.com", 443), timeout=3) 
    except OSError: 
        print(f"No internet connection - {datetime.now()}", flush=True)
        raise
    