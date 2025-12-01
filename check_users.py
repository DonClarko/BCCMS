from firebase_admin import db
from firebase_config import initialize_firebase

# Get all users
users_ref = db.reference('users')
users = users_ref.get() or {}

print(f"Total users in database: {len(users)}")
print("\nUsers:")
for uid, user in users.items():
    email = user.get('email', 'no-email')
    role = user.get('role', 'no-role')
    name = user.get('full_name', 'no-name')
    print(f"  - {name} ({email}) - Role: {role}")

print("\nOfficials only:")
officials = [u for u in users.values() if u.get('role') == 'official']
print(f"Total officials: {len(officials)}")
for official in officials:
    print(f"  - {official.get('full_name')} ({official.get('email')})")

print("\nResidents only:")
residents = [u for u in users.values() if u.get('role') == 'resident']
print(f"Total residents: {len(residents)}")
for resident in residents:
    print(f"  - {resident.get('full_name')} ({resident.get('email')})")
