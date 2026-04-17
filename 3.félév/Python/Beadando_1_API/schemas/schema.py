from pydantic import BaseModel, EmailStr, field_validator

'''

Útmutató a fájl használatához:

Az osztályokat a schema alapján ki kell dolgozni.

A schema.py az adatok küldésére
    és fogadására készített osztályokat tartalmazza.
Az osztályokban az adatok legyenek validálva.
 - az int adatok nem lehetnek negatívak.
 - az email mező csak e-mail formátumot fogadhat el.
 - Hiba esetén ValuErrort kell dobni, lehetőség szerint ezt a
   kliens oldalon is jelezni kell.

'''


ShopName = 'Bolt'


class User(BaseModel):
    id: int  # >=0
    name: str
    email: EmailStr

    @field_validator("id")
    def non_negative(cls, v, field):
        if v < 0:
            raise ValueError(f"{field.name} nem lehet negatív.")
        return v


class Basket(BaseModel):
    id: int
    user_id: int
    items: list["Item"]

    @field_validator("id", "user_id")
    def non_negative(cls, v, field):
        if v < 0:
            raise ValueError(f"{field.name} nem lehet negatív")
        return v


class Item(BaseModel):
    item_id: int
    name: str
    brand: str
    price: float
    quantity: int

    @field_validator("item_id", "price", "quantity")
    def non_negative(cls, v, field):
        if v < 0:
            raise ValueError(f"{field.name} nem lehet negatív.")
        return v
