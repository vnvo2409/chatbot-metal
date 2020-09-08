import sqlalchemy
import os

db = sqlalchemy.create_engine(
    os.getenv("DATABASE_URL"),
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=1800,
)

if __name__ == "__main__":
    print(db)
