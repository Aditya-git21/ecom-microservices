#!/bin/bash
API_URL="http://127.0.0.1:8001/products"

post() {
  curl -s -w "\nHTTP %{http_code}\n" -X POST "$API_URL" \
    -H "Content-Type: application/json" -d "$1"
}

post '{"name":"Mechanical Keyboard","description":"RGB tactile keyboard","price":89.99,"stock":50}'
post '{"name":"Wireless Ergonomic Mouse","description":"Vertical wireless mouse","price":59.99,"stock":100}'
post '{"name":"UltraWide 34in Monitor","description":"144Hz curved display","price":449.99,"stock":15}'
post '{"name":"Noise Cancelling Headphones","description":"Over-ear ANC headphones","price":199.99,"stock":30}'
post '{"name":"USB-C Hub","description":"8-in-1 aluminum hub","price":34.99,"stock":120}'
