import os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List

from app.database import engine, Base, get_db
from app.schemas import ProductCreate, ProductResponse, StockReduce
from app.models import Product

app = FastAPI(title="Product Service")

# Lifecycle initialization hook ensuring database tables exist
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 1. GET /health
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(select(1))
        return {"status": "UP", "service": "product-service"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Database connection failed: {str(e)}"
        )

# 2. POST /products
@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    new_product = Product(
        name=product_in.name,
        description=product_in.description,
        price=product_in.price,
        stock=product_in.stock
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

# 3. GET /products (With pagination limit & offset implemented)
@app.get("/products", response_model=List[ProductResponse])
async def list_products(limit: int = 10, offset: int = 0, db: AsyncSession = Depends(get_db)):
    query = select(Product).order_by(Product.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()

# 4. GET /products/{id}
@app.get("/products/{id}", response_model=ProductResponse)
async def get_product(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

# 5. PATCH /products/{id}/stock (Atomic Thread-Safe stock reduction)
@app.patch("/products/{id}/stock", response_model=ProductResponse)
async def reduce_stock(id: str, payload: StockReduce, db: AsyncSession = Depends(get_db)):
    # Atomic transaction query directly modifying database level state safely
    stmt = (
        update(Product)
        .where(Product.id == id)
        .where(Product.stock >= payload.quantity)
        .values(stock=Product.stock - payload.quantity)
        .returning(Product)
    )
    
    result = await db.execute(stmt)
    updated_product = result.scalar_one_or_none()
    
    if updated_product:
        await db.commit()
        return updated_product

    # Fallback to identify exact scenario profile when mutation updates zero matching instances
    exists_result = await db.execute(select(Product.stock).where(Product.id == id))
    current_stock = exists_result.scalar_one_or_none()
    
    if current_stock is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail=f"Insufficient stock available. Current stock: {current_stock}"
    )

