from typing import Dict
import reflex as rx

from obhonesty.constants import true_values

class User(rx.Base):
  nick_name: str
  first_name: str
  last_name: str
  email: str
  phone_number: str
  volunteer: bool
  away: bool
  diet: str
  allergies: str
  synced: bool
  prepaid_dinners_quantity: int

  @staticmethod
  def from_dict(x: Dict[str, str | bool | int]):
    return User(
      nick_name=x['nick_name'],
      first_name=x['first_name'],
      last_name=x['last_name'],
      email=x['email'],
      phone_number=x['phone_number'],
      volunteer=x["volunteer"],
      diet=x['diet'],
      allergies=x['allergies'],
      away=x["away"],
      synced=x["synced"],
      prepaid_dinners_quantity=x["prepaid_dinners_quantity"]
    )

