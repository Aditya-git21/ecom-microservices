# ecom-microservices
So this is the simple ecom-microservices appliication 
It had 3 independent services (user, order and product) 
1.User-svc(register/login), 2.Product-svc(list/create users) , 3.order-svc(creates an order , calls product svc over REST to check the price and stock)

Tech Stack:
FastAPI, PostgreSQL, Docker, Kubernetes

Status :
user service 
producr svc
order svc
docker 
k8s
frontend

How to run

source .venv/bin/activate
uvicorn app.main:app 
