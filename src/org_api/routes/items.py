from fastapi import APIRouter, Depends
from sqlmodel import select
from ichec_api.models import Item
from ichec_api.db import get_session

router = APIRouter()

@router.post("/items/", response_model=Item)
def create_item(item: Item, session=Depends(get_session)):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.get("/items/", response_model=list[Item])
def read_items(session=Depends(get_session)):
    return session.exec(select(Item)).all()
