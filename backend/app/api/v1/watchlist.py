from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.watchlist_item import WatchlistItem
from app.utils.security import get_current_user


router = APIRouter(prefix="/v1/watchlist", tags=["watchlist"])


class WatchlistItemOut(BaseModel):
    id: int
    symbol: str

    class Config:
        orm_mode = True


class WatchlistCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=32)


@router.get("/", response_model=List[WatchlistItemOut])
def list_watchlist(db: Session = Depends(get_db), user=Depends(get_current_user)):
    items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).order_by(WatchlistItem.id.desc()).all()
    return items


@router.post("/", response_model=WatchlistItemOut, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(payload: WatchlistCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    symbol = payload.symbol.upper()
    existing = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user.id, WatchlistItem.symbol == symbol)
        .first()
    )
    if existing:
        return existing
    item = WatchlistItem(user_id=user.id, symbol=symbol)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(item_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    item = db.query(WatchlistItem).filter(WatchlistItem.id == item_id, WatchlistItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    db.delete(item)
    db.commit()
    return None


