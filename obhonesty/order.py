from typing import Dict
import reflex as rx

from typing import Optional
from obhonesty.aux import safe_float_convert, value_or
from .constants import true_values

class Order(rx.Base):
  order_id: str
  user_nick_name: str
  time: str
  item: str
  quantity: float
  price: float
  total: float
  receiver: str
  diet: str
  allergies: str
  served: str
  tax_category: str
  comment: str
  paid: str | None
  paid_time: str | None
  method: str | None 
  checkout_staff: str | None

  @property
  def served_bool(self) -> bool:
    return self.served.lower() in true_values

  @property
  def paid_bool(self) -> bool:
    return self.paid == "TRUE"
  
  @staticmethod
  def from_dict(x: Dict[str, str]):
    return Order(
      order_id=x['order_id'],
      user_nick_name=x['user'],
      time=x['time'],
      item=x['item'],
      quantity=value_or(safe_float_convert(x['quantity']), 1.0),
      price=value_or(safe_float_convert(x['price']), 0.0),
      total=value_or(safe_float_convert(x['total']), 0.0),
      receiver=x['receiver'],
      diet=x['diet'],
      allergies=x['allergies'],
      served=x['served'],
      tax_category=x['tax_category'],
      comment=x['comment'],
      paid=x.get('paid'),
      paid_time=x.get('paid_time'),
      method=x.get('method'),
      checkout_staff=x.get('checkout_staff')
    )
  