from schemas.schema import User, Basket, Item
from fastapi.responses import JSONResponse  # , RedirectResponse
from fastapi import HTTPException  # , FastAPI, Request, Response, Cookie
from fastapi import APIRouter

from data.filehandler import (
    add_user,
    add_basket,
    add_item_to_basket,
    update_item,
    delete_item
)

from data.filereader import (
    get_user_by_id,
    get_basket_by_user_id,
    get_all_users,
    get_total_price_of_basket
)


'''

Útmutató a fájl használatához:

- Minden route esetén adjuk meg a response_modell értékét (típus)
- Ügyeljünk a típusok megadására
- A függvények visszatérési értéke JSONResponse() legyen
- Minden függvény tartalmazzon hibakezelést,
    hiba esetén dobjon egy HTTPException-t
- Az adatokat a data.json fájlba kell menteni.
- A HTTP válaszok minden esetben tartalmazzák a
  megfelelő Státus Code-ot, pl 404 - Not found, vagy 200 - OK

'''

routers = APIRouter()


@routers.post('/adduser', response_model=User)
def adduser(user: User) -> User:
    try:
        add_user(user.model_dump())
        return JSONResponse(content=user.model_dump(), status_code=200)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@routers.post('/addshoppingbag', response_model=str)
def addshoppingbag(userid: int) -> str:
    try:
        baskets = []
        users = get_all_users()
        for u in users:
            try:
                baskets += get_basket_by_user_id(u["id"])
            except ValueError:
                continue
        existing_ids = [b["id"] for b in baskets]
        new_id = max(existing_ids, default=0) + 1
        add_basket({"id": new_id, "user_id": userid, "items": []})
        return JSONResponse(content="Sikeres kosár hozzárendelés.", status_code=200) # noqa
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@routers.post('/additem', response_model=Basket)
def additem(userid: int, item: Item) -> Basket:
    try:
        add_item_to_basket(userid, item.model_dump())
        basket = get_basket_by_user_id(userid)
        return JSONResponse(content=basket[0], status_code=200)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@routers.put('/updateitem', response_model=Basket)
def updateitem(userid: int, itemid: int, updateItem: Item) -> Basket:
    try:
        update_item(userid, itemid, updateItem.model_dump())
        return JSONResponse(content=get_basket_by_user_id(userid), status_code=200) # noqa
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@routers.delete('/deleteitem', response_model=Basket)
def deleteitem(userid: int, itemid: int) -> Basket:
    try:
        delete_item(userid, itemid)
        return JSONResponse(content=get_basket_by_user_id(userid), status_code=200) # noqa
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@routers.get('/user', response_model=User)
def user(userid: int) -> User:
    try:
        u = get_user_by_id(userid)
        return JSONResponse(content=u, status_code=200)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@routers.get('/users', response_model=list[User])
def users() -> list[User]:
    try:
        us = get_all_users()
        return JSONResponse(content=us, status_code=200)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@routers.get('/shoppingbag', response_model=list[Item])
def shoppingbag(userid: int) -> list[Item]:
    try:
        sb = get_basket_by_user_id(userid)
        return JSONResponse(content=sb[0]["items"], status_code=200)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@routers.get('/getusertotal', response_model=float)
def getusertotal(userid: int) -> float:
    try:
        total = get_total_price_of_basket(userid)
        return JSONResponse(content=total, status_code=200)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
