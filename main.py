from typing import Union

from fastapi import FastAPI, HTTPException
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


db = SessionLocal()


@app.get("/items/{item_id}")
def read_item(item_id: int):
    try:
        item = db.query(Item).filter_by(id=item_id).first()
        if item:
            return item
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading task: {e}")


@app.post("/items/")
def create_item(item: ItemModel):
    try:
        new_task = Item(title=item.title, description=item.description)
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return {"message": "Item created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating task: {e}")


@app.put("/items/{item_id}")
def update_item(item_id: int, item: ItemModel):
    try:
        query = "UPDATE tasks SET title=%s, description=%s, completed=%s WHERE id=%s"
        values = (item.title, item.description, item.completed, item_id)
        db.query(query=query, values=values)
        db.commit()
        return {"message": "Item updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating task: {e}")


@app.get("/items/all/{table}")
def get_items():
    try:
        items = db.query(Item).all()
        json_answer = {}
        for item in items:
            json_answer[item.id] = item.title
        return json_answer
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading tasks: {e}")


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    try:
        item = read_item(item_id)
        if item:
            db.delete(item)
            db.commit()
            return {"message": "Item deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deleting task: {e}")
