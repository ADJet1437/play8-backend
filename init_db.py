"""
Script to initialize the database with tables and sample data.
Run this once to set up the database schema.
"""
from database import engine, SessionLocal, init_database as create_tables
from db_models import Machine
import uuid

def init_sample_data():
    # Create all tables
    print("Creating database tables...")
    create_tables()
    print("✓ Tables created successfully")
    
    # Create sample data
    db = SessionLocal()
    try:
        # Check if machines already exist
        existing_machines = db.query(Machine).count()
        if existing_machines == 0:
            print("Creating sample machines...")
            sample_machines = [
                Machine(
                    id=str(uuid.uuid4()),
                    name="Court 1",
                    location="Building A",
                    status="available"
                ),
                Machine(
                    id=str(uuid.uuid4()),
                    name="Court 2",
                    location="Building A",
                    status="available"
                ),
                Machine(
                    id=str(uuid.uuid4()),
                    name="Court 3",
                    location="Building B",
                    status="maintenance"
                ),
            ]
            for machine in sample_machines:
                db.add(machine)
            db.commit()
            print("✓ Sample machines created")
        else:
            print(f"✓ {existing_machines} machines already exist, skipping sample data")
    except Exception as e:
        print(f"✗ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n✓ Database initialization complete!")

if __name__ == "__main__":
    init_sample_data()

