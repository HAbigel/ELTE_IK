import json
import os
from typing import Dict, Any


'''
Útmutató a fájl függvényeinek a használatához

Új felhasználó hozzáadása:

new_user = {
    "id": 4,  # Egyedi felhasználó azonosító
    "name": "Szilvás Szabolcs",
    "email": "szabolcs@plumworld.com"
}

Felhasználó hozzáadása a JSON fájlhoz:

add_user(new_user)

Hozzáadunk egy új kosarat egy meglévő felhasználóhoz:

new_basket = {
    "id": 104,  # Egyedi kosár azonosító
    "user_id": 2,  # Az a felhasználó, akihez a kosár tartozik
    "items": []  # Kezdetben üres kosár
}

add_basket(new_basket)

Új termék hozzáadása egy felhasználó kosarához:

user_id = 2
new_item = {
    "item_id": 205,
    "name": "Szilva",
    "brand": "Stanley",
    "price": 7.99,
    "quantity": 3
}

Termék hozzáadása a kosárhoz:

add_item_to_basket(user_id, new_item)

Hogyan használd a fájlt?

Importáld a függvényeket a filehandler.py modulból:

from filehandler import (
    add_user,
    add_basket,
    add_item_to_basket,
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


def save_json(data: Dict[str, Any]) -> None:
    with open(JSON_FILE_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def add_user(user: Dict[str, Any]) -> None:
    data = load_json()
    if any(u["id"] == user["id"] for u in data["Users"]):
        raise ValueError(f"Már létezik {user['id']} ID-jú felhasználó")
        # f nem engedte ""
    data["Users"].append(user)
    save_json(data)


def add_basket(basket: Dict[str, Any]) -> None:
    data = load_json()
    if not any(u["id"] == basket["user_id"] for u in data["Users"]):
        raise ValueError(f"Nincs {basket['user_id']} ID-jú felhasználó")
    if any(b["id"] == basket["id"] for b in data["Baskets"]):
        raise ValueError(f"Már létezik {basket['id']} ID-jú kosár.")
    if any(basket["user_id"] == b["user_id"] for b in data["Baskets"]):
        raise ValueError(f"Már van kosara a {basket['user_id']} ID-jú felhasználónak.") # noqa
    basket["items"] = []
    data["Baskets"].append(basket)
    save_json(data)


def add_item_to_basket(user_id: int, item: Dict[str, Any]) -> None:
    data = load_json()
    has_basket = False
    for b in data["Baskets"]:
        if b["user_id"] == user_id:
            b["items"].append(item)
            has_basket = True
            break
    if has_basket is False:
        raise ValueError("Még nincs kosara a felhasználónak.")
    save_json(data)


################ noqa
def update_item(user_id: int, itemid: int, updateItem: Dict[str, Any]) -> None: # noqa
    data = load_json()
    has_item = False
    basket = None
    for b in data["Baskets"]:
        if b["user_id"] == user_id:
            basket = b
            break
    if basket is None:
        raise ValueError("Még nincs kosara a felhasználónak.")
    for ind, i in enumerate(basket["items"]):
        if i["item_id"] == itemid:
            basket["items"][ind] = updateItem
            has_item = True
            break
    if has_item is False:
        raise ValueError("Nincs ilyen item a felhasználó kosarában.")
    save_json(data)


def delete_item(user_id: int, itemid: int) -> None:
    data = load_json()
    has_item = False
    basket = None
    for b in data["Baskets"]:
        if b["user_id"] == user_id:
            basket = b
            break
    if basket is None:
        raise ValueError("Még nincs kosara a felhasználónak.")
    for i in basket["items"]:
        if i["item_id"] == itemid:
            has_item = True
            basket["items"].remove(i)
            break
    if has_item is False:
        raise ValueError("Nincs ilyen item a felhasználó kosarában.")
    save_json(data)
