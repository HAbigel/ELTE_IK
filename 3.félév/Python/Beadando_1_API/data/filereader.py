import json
import os
from typing import Dict, Any, List

'''
Útmutató a féjl használatához:

Felhasználó adatainak lekérdezése:

user_id = 1
user = get_user_by_id(user_id)
print(f"Felhasználó adatai: {user}")

Felhasználó kosarának tartalmának lekérdezése:

user_id = 1
basket = get_basket_by_user_id(user_id)
print(f"Felhasználó kosarának tartalma: {basket}")

Összes felhasználó lekérdezése:

users = get_all_users()
print(f"Összes felhasználó: {users}")

Felhasználó kosarában lévő termékek összárának lekérdezése:

user_id = 1
total_price = get_total_price_of_basket(user_id)
print(f"A felhasználó kosarának összára: {total_price}")

Hogyan futtasd?

Importáld a függvényeket a filehandler.py modulból:

from filereader import (
    get_user_by_id,
    get_basket_by_user_id,
    get_all_users,
    get_total_price_of_basket
)

 - Hiba esetén ValuErrort kell dobni, lehetőség szerint ezt a
   kliens oldalon is jelezni kell.

'''

# A JSON fájl elérési útja
JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), "data.json")


def load_json() -> Dict[str, Any]:
    if not os.path.exists(JSON_FILE_PATH):
        return {"Users": [], "Baskets": []}
    with open(JSON_FILE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def get_user_by_id(user_id: int) -> Dict[str, Any]:
    data = load_json()
    user = next((u for u in data["Users"] if u["id"] == user_id), None)
    if user is None:
        raise ValueError(f"Nincs {user_id} ID-jú felhasználó")
    return user


def get_basket_by_user_id(user_id: int) -> List[Dict[str, Any]]:
    data = load_json()
    basket = []
    for b in data["Baskets"]:
        if b["user_id"] == user_id:
            basket.append(b)
            break
    if not basket:
        raise ValueError(f"Nincs a {user_id} ID-jú felhasználónak kosara")
    return basket


def get_all_users() -> List[Dict[str, Any]]:
    data = load_json()
    return data["Users"]


def get_total_price_of_basket(user_id: int) -> float:
    basket = get_basket_by_user_id(user_id)
    """next(
        (b for b in data["Baskets"]
         if b["user_id"] == user_id),
        None)"""
    total_price = 0
    for i in basket[0]["items"]:
        total_price += i["price"]*i["quantity"]
    return total_price
