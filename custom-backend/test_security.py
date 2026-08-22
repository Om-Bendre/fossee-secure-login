"""
Small manual smoke-test checklist for the custom backend.

Run the API first, then use this file as a guide. It intentionally stays
simple so the security properties are easy to explain in an interview.
"""
CHECKS = [
    "Register a fourth user -> 201",
    "Login Alice -> 200 and token returned",
    "Wrong password repeatedly -> 401, then 429 during lockout",
    "GET /me -> only authenticated user's profile",
    "GET /files -> only authenticated user's files",
    "Alice requesting Bob's file -> 403",
    "Alice requesting a nonexistent file -> 404",
    "Download owned file -> actual bytes",
    "Logout -> 200",
    "Reuse the same JWT after logout -> 401",
]

if __name__ == "__main__":
    print("Manual security checks:")
    for number, check in enumerate(CHECKS, 1):
        print(f"{number}. {check}")
