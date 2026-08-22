from pathlib import Path
from app.database import SessionLocal
from app.models import File, User
from app.security import hash_password

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"

USERS = [
    ("alice@example.com", "Password123!", "Alice"),
    ("bob@example.com", "Password123!", "Bob"),
    ("carol@example.com", "Password123!", "Carol"),
]

def main():
    STORAGE_DIR.mkdir(exist_ok=True)
    db = SessionLocal()
    try:
        for email, password, name in USERS:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    password_hash=hash_password(password),
                    full_name=name,
                    display_name=name,
                    bio=f"{name}'s test profile",
                )
                db.add(user)
                db.flush()
            existing = db.query(File).filter(File.owner_id == user.id).count()
            if existing == 0:
                for number in (1, 2):
                    path = STORAGE_DIR / f"{user.display_name.lower()}-{number}.txt"
                    path.write_text(
                        f"FOSSEE demo file {number} belonging to {user.display_name}.\n",
                        encoding="utf-8",
                    )
                    db.add(File(
                        owner_id=user.id,
                        file_name=path.name,
                        mime_type="text/plain",
                        size_bytes=path.stat().st_size,
                        storage_path=str(path),
                    ))
        db.commit()
        print("Seed complete.")
        for email, password, _ in USERS:
            print(f"{email} / {password}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
