from database import Item, SessionLocal
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

app = FastAPI(title="Core Service")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"status": "ok", "service": "Core Service"}


@app.post("/items/")
def create_item(title: str, description: str, db: Session = Depends(get_db)):
    item = Item(title=title, description=description)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/items/{item_id}")
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item