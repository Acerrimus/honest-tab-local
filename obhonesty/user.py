from typing import Dict
import reflex as rx

from obhonesty.aux import lower_non_alpha_num
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

  @staticmethod
  def from_dict(x: Dict[str, str]):
    return User(
      nick_name=x['nick_name'],
      first_name=x['first_name'],
      last_name=x['last_name'],
      email=x['email'],
      phone_number=x['phone_number'],
      volunteer=lower_non_alpha_num(x['volunteer']) in true_values,
      diet=x['diet'],
      allergies=x['allergies'],
      away=lower_non_alpha_num(x['away']) in true_values
    )

