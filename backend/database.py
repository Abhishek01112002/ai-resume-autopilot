from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resume_app.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get database session
def get_db():
    print("DEBUG: Connecting to database...")
    try:
        db = SessionLocal()
        print("DEBUG: Database session created.")
        yield db
    except Exception as e:
        print(f"DEBUG: Database Error: {e}")
        raise
    finally:
        print("DEBUG: Closing database session.")
        try:
            db.close()
        except UnboundLocalError:
            pass
        except Exception as e:
            print(f"DEBUG: Error closing database: {e}")

