from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./ghost_inventory.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_and_migrate_db():
    """Ensure database tables exist and upgrade existing parts table columns if needed."""
    Base.metadata.create_all(bind=engine)
    
    # Inspect existing SQLite columns for parts table
    inspector = inspect(engine)
    if "parts" in inspector.get_table_names():
        existing_cols = {col["name"] for col in inspector.get_columns("parts")}
        
        # New columns to add if missing in existing ghost_inventory.db
        new_cols = {
            "seller_id": "INTEGER",
            "description": "TEXT",
            "manufacturer": "VARCHAR",
            "model_number": "VARCHAR",
            "part_number": "VARCHAR",
            "condition": "VARCHAR DEFAULT 'New'",
            "available_quantity": "INTEGER DEFAULT 1",
            "location_city": "VARCHAR",
            "location_state": "VARCHAR",
            "latitude": "FLOAT",
            "longitude": "FLOAT",
            "estimated_dispatch_days": "INTEGER DEFAULT 1",
            "last_stock_confirmed_at": "DATETIME",
            "verification_status": "VARCHAR DEFAULT 'Unverified'"
        }
        
        with engine.connect() as conn:
            for col_name, col_type in new_cols.items():
                if col_name not in existing_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE parts ADD COLUMN {col_name} {col_type};"))
                        conn.commit()
                    except Exception as e:
                        print(f"Migration column add {col_name} skipped: {e}")
