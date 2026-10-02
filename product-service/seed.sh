#!/bin/bash
echo "🚀 Seeding products catalog into products_db..."
echo "------------------------------------------------"

API_URL="http://127.0.0.1:8001/products"

curl -X POST "$API_URL" -H "Content-Type: application/json" -d '{
  "name": "Mechanical Keyboard",
  "description": "RGB Backlit tactile mechanical keyboard",
  "price": 89.99,
  "stock": 50
}'
echo -e "\n"

curl -X POST "$API_URL" -H "Content-Type: application/json" -d '{
  "name": "Wireless Ergonomic Mouse",
  "description": "High-precision vertical wireless mouse",
  "price": 59.99,
  "stock": 100
}'
echo -e "\n"

curl -X POST "$API_URL" -H "Content-Type: application/json" -d '{
  "name": "UltraWide 34in Monitor",
  "description": "144Hz curved ultrawide gaming display",
  "price": 449.99,
  "stock": 15
}'
echo -e "\n"

curl -X POST "$API_URL" -H "Content-Type: application/json" -d '{
  "name": "Noise Cancelling Headphones",
  "description": "Over-ear active noise cancelling headphones",
  "price": 199.99,
  "stock": 30
}'
echo -e "\n"

curl -X POST "$API_URL" -H "Content-Type: application/json" -d '{
  "name": "USB-C Multi-port Hub",
  "description": "8-in-1 space gray aluminum adapter hub",
  "price": 34.99,
  "stock": 120
}'

echo -e "\n\n✅ Catalog seeding complete!"

