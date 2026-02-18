"""
Run once to create the database tables and insert test users.

Usage:
    uv run python testusers.py
"""

import bcrypt

from database import Base, engine, SessionLocal
from models import User


def seed():
    # Create all tables defined by Base subclasses (just 'users' for now).
    # If the table already exists, this is a no-op — it won't drop/recreate it.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    test_users = [
        {"email": "lawton@test.com", "password": "testpass123"},
        {"email": "alice@test.com", "password": "testpass123"},
        {"email": "bob@test.com", "password": "testpass123"},
    ]

    try:
        for user_data in test_users:
            # Check if user already exists so the script is safe to re-run
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if existing:
                print(f"  Skipped {user_data['email']} (already exists)")
                continue

            user = User(
                email=user_data["email"],
                hashed_password=bcrypt.hashpw(
                    user_data["password"].encode(), bcrypt.gensalt()
                ).decode(),
            )
            db.add(user)
            print(f"  Added {user_data['email']}")

        db.commit()
        print("\nDone! Users seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"\nError: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
