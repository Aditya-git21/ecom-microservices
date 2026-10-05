from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from . import clients, models, schemas
from .auth import get_current_user_id
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Order Service")


def mark_failed(db: Session, order: models.Order) -> None:
    order.status = "FAILED"
    db.commit()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/orders", response_model=schemas.OrderOut,
          status_code=status.HTTP_201_CREATED)
def create_order(
    payload: schemas.OrderCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # 1. Look up the product (price + stock) over REST
    try:
        product = clients.get_product(payload.product_id)
    except clients.ProductNotFound:
        raise HTTPException(status_code=404, detail="Product not found")
    except clients.ProductServiceTimeout:
        raise HTTPException(status_code=504, detail="Product service timed out")
    except clients.ProductServiceUnavailable:
        raise HTTPException(status_code=503, detail="Product service unavailable")

    # 2. Cheap early check. Stock may still change, so step 4 is the real check.
    if product["stock"] < payload.quantity:
        raise HTTPException(status_code=409, detail="Insufficient stock")

    # 3. Save the order as PENDING first, so there is always a trail
    unit_price = product["price"]
    order = models.Order(
        user_id=user_id,                        # from the token, never the body
        product_id=payload.product_id,
        quantity=payload.quantity,
        unit_price=unit_price,
        total=unit_price * payload.quantity,
        status="PENDING",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 4. Atomic stock reduction in product-service
    try:
        clients.reduce_stock(payload.product_id, payload.quantity)
    except clients.InsufficientStock:
        mark_failed(db, order)
        raise HTTPException(status_code=409, detail="Insufficient stock")
    except clients.ProductNotFound:
        mark_failed(db, order)
        raise HTTPException(status_code=404, detail="Product not found")
    except clients.ProductServiceTimeout:
        # Outcome unknown: stock may or may not have been reduced.
        # Leave PENDING so it can be reconciled instead of guessing.
        raise HTTPException(
            status_code=504,
            detail=f"Product service timed out. Order {order.id} is PENDING.",
        )
    except clients.ProductServiceUnavailable:
        mark_failed(db, order)
        raise HTTPException(status_code=503, detail="Product service unavailable")

    # 5. Success
    order.status = "CONFIRMED"
    db.commit()
    db.refresh(order)
    return order


@app.get("/orders", response_model=List[schemas.OrderOut])
def list_my_orders(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Order)
        .filter(models.Order.user_id == user_id)
        .order_by(models.Order.id.desc())
        .all()
    )


@app.get("/orders/{order_id}", response_model=schemas.OrderOut)
def get_my_order(
    order_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    order = db.get(models.Order, order_id)
    # 404 (not 403) for other people's orders, so we don't reveal they exist
    if order is None or order.user_id != user_id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
