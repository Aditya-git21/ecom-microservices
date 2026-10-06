#!/bin/bash
U=http://127.0.0.1:8000
P=http://127.0.0.1:8001
O=http://127.0.0.1:8002
EMAIL="test$RANDOM@example.com"
PASS="password123"
H="Content-Type: application/json"

call() { curl -s -w "  -> HTTP %{http_code}\n" "$@"; echo; }

echo "=== 1. health (expect ok x3)"
for url in $U $P $O; do curl -s $url/health; echo; done

echo "=== 2. register (201)"
call -X POST $U/register -H "$H" -d "{\"email\":\"$EMAIL\",\"name\":\"Test\",\"password\":\"$PASS\"}"

echo "=== 3. duplicate register (409)"
call -X POST $U/register -H "$H" -d "{\"email\":\"$EMAIL\",\"name\":\"Test\",\"password\":\"$PASS\"}"

echo "=== 4. wrong password (401)"
call -X POST $U/login -H "$H" -d "{\"email\":\"$EMAIL\",\"password\":\"wrongpass1\"}"

echo "=== 5. login (200) and /me"
TOKEN=$(curl -s -X POST $U/login -H "$H" -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
call $U/me -H "Authorization: Bearer $TOKEN"

echo "=== 6. stock before"
call $P/products/1

echo "=== 7. place order, qty 2 (201, CONFIRMED)"
call -X POST $O/orders -H "Authorization: Bearer $TOKEN" -H "$H" -d '{"product_id":1,"quantity":2}'

echo "=== 8. stock after (should be 2 lower)"
call $P/products/1

echo "=== 9. my orders (200)"
call $O/orders -H "Authorization: Bearer $TOKEN"

echo "=== 10. no token (401)"
call -X POST $O/orders -H "$H" -d '{"product_id":1,"quantity":1}'

echo "=== 11. garbage token (401)"
call -X POST $O/orders -H "Authorization: Bearer abc.def.ghi" -H "$H" -d '{"product_id":1,"quantity":1}'

echo "=== 12. unknown product (404)"
call -X POST $O/orders -H "Authorization: Bearer $TOKEN" -H "$H" -d '{"product_id":999,"quantity":1}'

echo "=== 13. too much stock (409)"
call -X POST $O/orders -H "Authorization: Bearer $TOKEN" -H "$H" -d '{"product_id":1,"quantity":999999}'

echo "=== 14. quantity 0 (422)"
call -X POST $O/orders -H "Authorization: Bearer $TOKEN" -H "$H" -d '{"product_id":1,"quantity":0}'

echo "=== 15. race: product with stock 1, two orders at once (one 201, one 409)"
PID=$(curl -s -X POST $P/products -H "$H" -d '{"name":"Race Item","price":10.00,"stock":1}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
curl -s -w "  -> HTTP %{http_code}\n" -X POST $O/orders -H "Authorization: Bearer $TOKEN" -H "$H" -d "{\"product_id\":$PID,\"quantity\":1}" &
curl -s -w "  -> HTTP %{http_code}\n" -X POST $O/orders -H "Authorization: Bearer $TOKEN" -H "$H" -d "{\"product_id\":$PID,\"quantity\":1}" &
wait
echo
call $P/products/$PID
