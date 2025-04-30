from typing import Dict
import reflex as rx

from honest_tab.aux import value_or, safe_float_convert

class Item(rx.Base):
  name: str
  price: float
  description: str
  tax_category: str

  @staticmethod
  def from_dict(x: Dict[str, str]):
    return Item(
      name=x['name'],
      price=value_or(safe_float_convert(x['price']), 0.0),
      description=x['description'],
      tax_category=x['tax_category']
    )
