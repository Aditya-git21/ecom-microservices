# what I built today 

root project folder strudture 
git hub repo 
files setup 

1.User-svc
 
• database.py: Initializes SQLAlchemy create_engine, sessionmaker, and the Base class.

• models.py: Contains the User class mapping directly to your Postgres/MySQL table columns (id, email, password_hash, etc.).

• schemas.py: Contains Pydantic models like UserCreate (validates incoming JSON data on registration) and UserOut (filters out the password hash before sending the user data back to the client).

• security.py: Functions for hashing passwords using Passlib/Bcrypt and creating/decoding JWT access tokens.

• main.py: The entrypoint that spins up FastAPI, defines endpoints (/register, /login, /me), and ties all components together.


curl can register, login, and call /me with the token
 Wrong password gives 401, duplicate email gives 409
 Password hash is visible in the DB but never in any response

2. Products-service (products_db:8001) 


using decimal over float for the price in products table

public endpoints(get/products), and protected endpoints(post/products, patch)

stock reduction : using only 1 single endpoint sql , db operation bcoz 2 causes the system integrity error when both user checkig stock on a single product simultanesly i.e The Problem with Two Calls (GET then PATCH):** It creates a **race condition** (Time-of-Check to Time-of-Use bug). If Product X has 1 item left in stock, and User A and User B check stock simultaneously, both `GET` calls return `stock = 1`. Both services then issue a `PATCH` to decrement stock. The stock drops to `-1`, and an item is double-sold, breaking inventory integrity. 

# Errors I hit n how i fix the 

many linux cmd errors n confusions  - took help n google n fixed 

url mapping error 


# Things I didn't understand yet 

I dont understand the pyhton n why venv is needed here 

JWT tokens (auth how its works)
