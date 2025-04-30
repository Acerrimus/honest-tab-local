from typing import Dict
import reflex as rx

from typing import Optional
from honest_tab.aux import safe_float_convert, value_or

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
      comment=x['comment']
    )
  