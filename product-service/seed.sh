#!/bin/bash
echo "🚀 Seeding products catalog into products_db..."
echo "------------------------------------------------"

curl -X POST http://127.0.0 -H "Content-Type: application/json" -d '{"name": "Mechanical Keyboard", "description": "RGB Backlit tactile switches", "price": 89.99, "stock": 50}'
echo -e "\n"
curl -X POST http://127.0.0 -H "Content-Type: application/json" -d '{"name": "Wireless Ergonomic Mouse", "description": "High precision optical sensor", "price": 49.50, "stock": 120}'
echo -e "\n"
curl -X POST http://127.0.0 -H "Content-Type: application/json" -d '{"name": "UltraWide 34in Monitor", "description": "144Hz curved display panel", "price": 349.99, "stock": 15}'
echo -e "\n"
curl -X POST http://127.0.0 -H "Content-Type: application/json" -d '{"name": "Noise Cancelling Headphones", "description": "Over-ear wireless audio crisp profile", "price": 199.00, "stock": 8}'
echo -e "\n"
curl -X POST http://127.0.0 -H "Content-Type: application/json" -d '{"name": "USB-C Multi-port Hub", "description": "6-in-1 aluminum space gray adapter", "price": 24.95, "stock": 200}'

echo -e "\n\n✅ Catalog seeding complete!"
