import sqlalchemy
import os

db = sqlalchemy.create_engine(
    sqlalchemy.engine.url.URL(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database="vovannghia",
    ),
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=1800,
)

if __name__ == "__main__":
    print(db)
