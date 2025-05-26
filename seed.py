from app.main import SessionLocal, User

db = SessionLocal()

# Add dummy users
dummy_users = [
    User(name="Alice", email="alice@example.com"),
    User(name="Bob", email="bob@example.com"),
]

# Insert only if DB is empty
if not db.query(User).first():
    db.add_all(dummy_users)
    db.commit()

db.close()
