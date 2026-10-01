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


# Errors I hit n how i fix the 

many linux cmd errors n confusions  - took help n google n fixed 


# Things I didn't understand yet 

I dont understand the pyhton n why venv is needed here 
