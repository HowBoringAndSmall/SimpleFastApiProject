from typing import Union

from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel


app = FastAPI()

SQLALCHEMY_DATABASE_URL = "sqlite:///./items.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), index=True)
    description = Column(String(255))
    completed = Column(Boolean, default=False)


Base.metadata.create_all(bind=engine)


class ItemModel(BaseModel):
    title: str
    description: str
    completed: Union[bool, None] = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ItemNotFoundException(Exception):
    pass


class ValidationException(Exception):
    pass


class DatabaseException(Exception):
    pass


def validate_data(data):
    if not data.title:
        raise ValidationException('Title is required')
    if not data.description:
        raise ValidationException('Description is required')


@app.get("/items/{item_id}")
def read_item(item_id: int, db=Depends(get_db)):
    try:
        item = db.query(Item).filter_by(id=item_id).first()
        if item is None:
            raise ItemNotFoundException()
        return {"item": item}
    except ItemNotFoundException:
        return {'404': {'error': 'Item not found'}}
    except Exception as e:
        return {'505': {'error': str(e)}}


@app.post("/items/")
def create_item(item: ItemModel, db=Depends(get_db)):
    try:
        new_task = Item(title=item.title, description=item.description)
        validate_data(new_task)
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return new_task
    except ValidationException:
        return {'422': {'error': 'Invalid data'}}
    except DatabaseException:
        return {'500': {'error': 'Database error'}}
    except Exception as e:
        return {'422': {'error': str(e)}}


@app.put("/items/{item_id}")
def update_item(item_id: int, item: ItemModel):
    return {"item_name": item.title, "item_price": item.description, "item_id": item_id}


@app.get("/items/all/{table}")
def get_items(db=Depends(get_db)):
    items = db.query(Item).all()
    json_answer = {}
    for item in items:
        json_answer[item.id] = item.title
    return json_answer


@app.delete("/items/{item_id}")
def delete_item(item_id: int, db=Depends(get_db)):
    record = read_item(item_id, db)
    item = record["item"]
    if item:
        db.delete(item)
        db.commit()
        return True
    return False
