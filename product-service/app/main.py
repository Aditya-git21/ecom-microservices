from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

# Creates tables that don't exist yet (does NOT modify existing ones)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Product Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/products", response_model=schemas.ProductOut,
          status_code=status.HTTP_201_CREATED)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    product = models.Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@app.get("/products", response_model=List[schemas.ProductOut])
def list_products(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Product)
        .order_by(models.Product.id)
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.get("/products/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/products/{product_id}/reduce-stock")
def reduce_product_stock(
    product_id: int,
    payload: schemas.StockReductionRequest,
    db: Session = Depends(get_db),
):
    # One atomic statement: check and decrement happen together in Postgres
    stmt = (
        update(models.Product)
        .where(models.Product.id == product_id)
        .where(models.Product.stock >= payload.quantity)
        .values(stock=models.Product.stock - payload.quantity)
        .returning(models.Product.stock)
    )
    row = db.execute(stmt).fetchone()

    if row is None:
        db.rollback()
        product = db.get(models.Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available stock is {product.stock}.",
        )

    db.commit()
    return {
        "message": "Stock reduced successfully",
        "reduced_by": payload.quantity,
        "remaining_stock": row[0],
    }
