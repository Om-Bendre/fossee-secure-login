# FOSSEE Secure Login System

A small authentication, authorization, and file-access system implemented twice using two different backends:

1. **Custom backend** — FastAPI + PostgreSQL + SQLAlchemy
2. **Managed backend** — Appwrite

Both implementations use the **provided HTML testing client**.

The goal of this project is correctness, security, clear architectural decisions, and extensibility — rather than UI design.

---

## What This Project Does

The system provides:

- User registration with email and password
- Login with authentication
- Logout with actual server-side/session invalidation
- Protected user profile endpoint (`/me`)
- Per-user file listing
- Per-file authorization
- File downloading
- Three seeded test users with two files each
- Bcrypt password hashing in the custom backend
- Generic login error messages to reduce account enumeration
- Failed-login lockout
- Bearer-token authentication in the custom backend
- Appwrite-managed authentication and permissions
- A small reusable ABAC permission engine in the custom backend
- Automated tests for the ABAC permission engine

---

## Custom Backend

The custom implementation is built using:

```
FastAPI
PostgreSQL
SQLAlchemy
Alembic
JWT
bcrypt
```

### Custom Backend Architecture

The request flow is:

```
                     index.html
                         |
                         v
                  FastAPI routers
                         |
             +-----------+-----------+
             |           |           |
          auth.py     users.py    files.py
             |           |           |
             +-----------+-----------+
                         |
                         v
                  Authentication
                         |
             +-----------+-----------+
             |                       |
        Verify JWT             Check revocation
        signature              using JTI
             |                       |
             +-----------+-----------+
                         |
                         v
                    Load User
                         |
                         v
                   Authorization
                         |
              Subject + Resource
                    + Action
                         |
                         v
                     Policy
                         |
                  ALLOW / DENY
                         |
                         v
                  PostgreSQL
                  + local files
```

Authentication answers:

> Who is making the request?

Authorization answers:

> Is that user allowed to perform this action on this resource?

These are intentionally kept as separate responsibilities.

---

### ABAC Permission System

The assignment only requires users to access their own files.

A simple ownership check would have been enough:

```python
file.owner_id == current_user.id
```

However, I implemented a small reusable Attribute-Based Access Control (ABAC) permission layer in the custom backend.

The reason is **extensibility**.

A real system could eventually require rules such as:

- An owner can read their own file.
- An instructor can read files belonging to students assigned to that instructor.
- A project administrator can manage files belonging to their project.
- A user can download a file only if the file is marked downloadable.

Hardcoding each new rule directly into the file routes would make the authorization logic difficult to maintain.

Instead, the permission engine models:

```
Subject
    |
    | Who is requesting access?
    v

Resource
    |
    | What is being accessed?
    v

Action
    |
    | What are they trying to do?
    v

Policy
    |
    v

ALLOW / DENY
```

The generic engine does not know anything about users, files, students, instructors, or projects.

### ABAC Decision Rules

The permission engine follows three rules:

1. Explicit **DENY** always wins.
2. If there is no DENY and at least one policy returns ALLOW, the request is allowed.
3. If no applicable policy allows the request, access is denied by default.

This provides a fail-safe default.

### Current ABAC Policy

The current application intentionally has only **one** concrete policy:

> A user can access a file only when the user owns that file.

This means the ABAC layer does not give the application additional permissions beyond the assignment requirements. It simply provides an extensible authorization architecture. New policies can be added later without changing the core authentication system.

### ABAC Code Structure

```
custom-backend/app/authorization/
├── core/
│   ├── subject.py
│   ├── resource.py
│   ├── action.py
│   ├── policy.py
│   └── engine.py
│
├── adapters.py
└── policies.py
```

The `core/` package is intentionally generic. It does not depend directly on the application's `User` or `File` models. The adapters connect application-specific objects to the generic authorization engine.

### Why ABAC Instead of Hardcoded RBAC?

RBAC primarily answers:

> What can this role do?

For example:

```
Admin  → read/write everything
User   → read own files
```

That works well when permissions map cleanly to stable roles.

ABAC instead evaluates attributes and relationships:

```
Subject attributes
        +
Resource attributes
        +
Action
        +
Policy
        ↓
     Decision
```

This makes ABAC better suited to rules involving ownership, relationships, resource properties, project membership, or other contextual attributes.

For this assignment, the actual policy remains simple:

```
user owns file → ALLOW
otherwise      → DENY
```

The framework is generic, while the application's current policy remains minimal.

---

### JWT Authentication

The custom backend uses short-lived JWT access tokens.

The test client already expects:

```
Authorization: Bearer <JWT>
```

so JWT authentication fits naturally with the supplied client.

A JWT contains:

| Claim | Meaning |
|---|---|
| `sub` | identifies the user |
| `jti` | uniquely identifies the token |
| `exp` | specifies the expiration time |

**Why JWT?**

JWT was chosen because:

- It is simple for the supplied API client.
- The API can validate the token without storing the full token.
- The token carries the authenticated user's identity.
- The implementation remains small and easy to understand.

However, JWTs normally remain valid until expiry even after a client logs out. That creates a problem for the assignment because logout should actually invalidate the authentication session.

### Server-Side Logout Using JTI Revocation

The custom backend solves this using the JWT's `jti`.

The logout flow is:

```
Client sends JWT
       |
       v
Validate JWT
       |
       v
Read jti + exp
       |
       v
Store JTI in revoked_tokens
       |
       v
Future protected request
       |
       v
Check revoked_tokens
       |
       +---- Found ----> 401
       |
       +---- Not found -> Continue
```

The actual JWT is not stored in the database. Only its unique identifier (`jti`) and expiration time are stored. Expired revoked-token records can be cleaned up periodically in a production deployment.

This means logout invalidates the token on the server rather than simply removing it from the browser.

---

### User Data Isolation

The application enforces data isolation at the authorization layer.

For `GET /files`, the database query only retrieves files owned by the authenticated user:

```python
File.owner_id == current_user.id
```

For `GET /files/{id}` and `GET /files/{id}/download`, the application verifies that the requested file belongs to the current user before returning the resource.

The expected outcomes are:

```
File does not exist
        ↓
      404

File exists but belongs to another user
        ↓
      403

File exists and belongs to current user
        ↓
      200
```

This prevents a user from simply changing a file ID and accessing another user's file.

---

### Password and Login Security

The custom backend applies several basic security controls.

**Password hashing**

Passwords are stored as bcrypt hashes. The original password is never stored.

**Generic authentication errors**

Failed login attempts return:

```
Invalid email or password
```

for both an unknown email and an incorrect password. This avoids exposing an obvious account-enumeration signal.

**Failed-login lockout**

After five failed login attempts for the same email:

```
5 failed attempts
        ↓
60 second lockout
        ↓
429 Too Many Requests
```

The current implementation keeps this state in memory. For a multi-instance production deployment, this should be moved to a shared system such as Redis.

---

### CORS Security

The custom backend uses an explicit CORS allowlist rather than wildcard configuration.

The currently trusted origins are:

```
http://localhost:5500
http://127.0.0.1:5500
```

The API also restricts the allowed methods and headers to those required by the application:

- **Methods:** `GET`, `POST`
- **Headers:** `Authorization`, `Content-Type`

Cookie credentials are disabled because the custom implementation uses Bearer-token authentication rather than cookie-based sessions.

This is intentionally restrictive for the current application. In a production deployment, the allowlist would be changed to the actual trusted frontend origins.

CORS is treated as a browser-side security boundary, not as an authentication or authorization mechanism. Authentication is enforced by JWT validation, while authorization and resource ownership are enforced server-side.

---

### Seed Test Accounts

The custom backend provides three seeded users:

```
alice@example.com / Password123!
bob@example.com   / Password123!
carol@example.com / Password123!
```

Each user has two sample files.

To recreate the data:

```bash
cd custom-backend
python seed.py
```

The files are stored under:

```
custom-backend/storage/
```

---

### Custom Backend Setup

**1. Create a virtual environment**

```bash
python -m venv venv2
source venv2/bin/activate
pip install -r requirements.txt
```

**2. Configure PostgreSQL**

Create the PostgreSQL database and user required by the application.

Create a local `.env` file:

```env
DATABASE_URL=postgresql+psycopg2://fossee_app:YOUR_PASSWORD@localhost:5432/fossee_auth
JWT_SECRET=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Generate a secure JWT secret with:

```bash
openssl rand -hex 32
```

Never commit the real `.env` file.

**3. Run migrations**

```bash
alembic upgrade head
```

The migration history contains the development evolution of the database schema, ending with the UUID-based schema used by the application.

**4. Seed the database**

```bash
python seed.py
```

**5. Start the backend**

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```
http://localhost:8000
```

Interactive API documentation:

```
http://localhost:8000/docs
```

---

### Running the Provided Test Client

The project uses the provided `index.html` testing client. No separate GUI was created.

For the custom backend, serve the frontend:

```bash
cd frontend
python -m http.server 5500
```

Then open:

```
http://localhost:5500
```

Select **Custom REST backend** and use:

```
http://localhost:8000
```

Do not open the HTML file directly using `file://`. The testing client should be served through HTTP.

---

### API Routes

The custom backend exposes:

```
POST /register
POST /login
POST /logout

GET /me

GET /files
GET /files/{id}
GET /files/{id}/download
```

Protected routes use:

```
Authorization: Bearer <JWT>
```

---

### Automated Tests

The ABAC permission engine has automated tests that do not require PostgreSQL or a running server.

The tests verify:

- A matching policy correctly allows access.
- A non-matching policy denies access.
- Access is denied when no policy applies.
- An explicit DENY overrides an ALLOW.
- The default behavior is fail-safe.

Run:

```bash
pytest -q
```

The test suite is intentionally focused on the reusable authorization engine.

---

### Manual Security Verification

The following checklist verifies the complete custom backend.

**1. Registration**

Register a fourth user.

Expected: `201 Created`

**2. Login**

Login as Alice.

Expected: `200 OK`, JWT returned

**3. Failed-login protection**

Enter an incorrect password five times.

Expected:
```
401
401
401
401
401
429
```

During the lockout, even the correct password should continue returning `429` until the lockout expires.

**4. Profile**

Call `GET /me`.

Expected: `200`, Alice's profile

**5. File listing**

Call `GET /files`.

Expected: only Alice's files

**6. Authorization test**

While authenticated as Alice, request one of Bob's file IDs.

Expected: `403`

**7. Missing resource**

Request a completely nonexistent file ID.

Expected: `404`

**8. File download**

Download one of Alice's files.

Expected: `200`, file downloaded

**9. Logout**

Logout while authenticated.

Expected: `200`

**10. Reuse old JWT**

Reuse the exact JWT from before logout against `GET /me`.

Expected: `401`

This final test proves that logout is enforced server-side through JTI revocation rather than only clearing the token on the client.

---

## Appwrite Implementation

The second implementation uses Appwrite as the managed backend.

Appwrite handles the authentication/session and permission infrastructure instead of reproducing those mechanisms in application code.

The Appwrite implementation contains:

```
appwrite/
├── appwrite-adapter.js
├── seed-appwrite.js
├── SETUP.md
└── .env
```

The API key is stored only in the local `appwrite/.env` and must never be committed.

### Appwrite Resources

The Appwrite project contains:

```
Project
│
├── Web platform
│
├── Database
│   └── files
│       ├── ownerId
│       ├── fileName
│       ├── mimeType
│       ├── sizeBytes
│       ├── storageFileId
│       └── uploadedAt
│
└── Storage
    └── user-files
```

Row-level security is enabled for the file data. File-level security is enabled for storage. Each seeded user's files are granted read access only to that user.

### Appwrite Seed Data

The Appwrite seed script creates:

```
Alice
├── alice-1.txt
└── alice-2.txt

Bob
├── bob-1.txt
└── bob-2.txt

Carol
├── carol-1.txt
└── carol-2.txt
```

Run:

```bash
cd appwrite
npm install
node seed-appwrite.js
```

The Appwrite API key required by the seed script is loaded from `appwrite/.env`. The key is never exposed to the browser.

---

### What Appwrite Handles vs What I Built

| Area | Custom Backend | Appwrite |
|---|---|---|
| Password storage | bcrypt in application code | Appwrite |
| Authentication | JWT implementation | Appwrite |
| Sessions | JWT + JTI revocation | Appwrite sessions |
| Logout | Revoked-token table | Session deletion |
| User lookup | SQLAlchemy | Appwrite Account API |
| File ownership | Custom ABAC policy | Appwrite permissions |
| File storage | Local storage directory | Appwrite Storage |
| Rate limiting | In-memory lockout | Platform controls |
| Authorization | Generic ABAC engine | Appwrite permission system |
| Test-user seeding | Python script | Node.js Appwrite script |

The custom ABAC engine is intentionally **not** copied into the Appwrite implementation. Appwrite already provides its own permission system, so the managed implementation uses the platform's native security model.

This keeps the comparison honest:

- **Custom backend** → Build the security mechanisms
- **Appwrite** → Configure and use the managed security mechanisms

---

### Why the Two Implementations Are Different

The purpose of implementing both versions is not to make them internally identical.

The custom backend demonstrates understanding of:

- Authentication — JWTs, token revocation, password hashing
- Authorization — ABAC, resource ownership
- CORS
- Database isolation

The Appwrite implementation demonstrates how those responsibilities can be delegated to a managed backend while still configuring application-specific permissions correctly.

---

## Future Improvements

Given more time, I would improve the system by adding:

- Redis-backed rate limiting
- Shared distributed token revocation
- Automatic cleanup of expired revoked-token records
- Refresh-token/session rotation
- More automated integration tests
- End-to-end security tests against PostgreSQL
- A real file-upload endpoint
- File type and size validation
- Cloud object storage for the custom backend
- CI/CD with automated security and test checks
- More application-specific ABAC policies
- Production deployment configuration

These improvements are intentionally outside the current MVP so that the implementation remains focused on the assignment requirements while providing a clear path for extension.

---

## Project Structure

```
fossee-secure-login/
│
├── custom-backend/
│   ├── app/
│   │   ├── authorization/
│   │   ├── routers/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   ├── deps.py
│   │   └── main.py
│   │
│   ├── alembic/
│   ├── storage/
│   ├── seed.py
│   └── requirements.txt
│
├── appwrite/
│   ├── appwrite-adapter.js
│   ├── seed-appwrite.js
│   ├── SETUP.md
│   └── .env.example
│
├── frontend/
│   └── index.html
│
├── tests/
│   └── test_security.py
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Final Design Philosophy

The project intentionally keeps authentication and authorization separate.

```
Authentication
      ↓
Who are you?
      ↓
Authenticated User
      ↓
Authorization
      ↓
What are you allowed to do?
      ↓
ALLOW / DENY
      ↓
Resource
```

The custom backend demonstrates these mechanisms explicitly. The Appwrite backend demonstrates how the same application requirements can be implemented using a managed authentication, database, and storage platform.

The implementation therefore focuses on both security correctness and architectural reasoning, rather than simply making the login form work.