from typing import Dict
import reflex as rx

class User(rx.Base):
  nick_name: str
  first_name: str
  last_name: str
  email: str
  phone_number: str
  address: str
  volunteer: bool
  away: bool
  diet: str
  allergies: str

  @staticmethod
  def from_dict(x: Dict[str, str]):
    return User(
      nick_name=x['nick_name'],
      first_name=x['first_name'],
      last_name=x['last_name'],
      email=x['email'],
      phone_number=x['phone_number'],
      address=x['address'],
      volunteer=x['volunteer'] == 'yes',
      away=x['away'] == 'yes',
      diet=x['diet'],
      allergies=x['allergies']
    )

