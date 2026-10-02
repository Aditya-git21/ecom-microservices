import uuid
from sqlalchemy import Column, String, Text, Numeric, Integer, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # Using numeric data type to prevent floating-point representation failures
    price = Column(Numeric(10, 2), nullable=False, server_default="0.00")
    stock = Column(Integer, nullable=False, server_default="0")

    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"), onupdate=text("NOW()"))

