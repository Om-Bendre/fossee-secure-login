# Appwrite setup

This folder implements the managed-backend version of the assignment.

## 1. Create a project

Create an Appwrite project and note:

- Project ID
- API endpoint (usually `https://cloud.appwrite.io/v1`)

Enable the Web platform for the origin serving `frontend/index.html`, for example:

- `http://localhost:5500`

## 2. Authentication

Use Appwrite Account email/password authentication.

The web adapter uses:

- `account.create()` for registration
- `account.createEmailPasswordSession()` for login
- `account.get()` for the current user
- `account.deleteSession({ sessionId: "current" })` for logout

Appwrite handles password storage/hashing and session management.

## 3. Database

Create a database and a collection named `files`.

Create these attributes:

| Attribute | Type | Required |
|---|---|---|
| ownerId | string | yes |
| fileName | string | yes |
| mimeType | string | yes |
| sizeBytes | integer | yes |
| storageFileId | string | yes |
| uploadedAt | datetime | yes |

Enable document-level security.

Do not grant the collection a public read permission. Each document should grant read access only to its owner.

## 4. Storage

Create a bucket named `user-files`.

Enable file-level security.

Do not give the bucket public read access. Seeded files should grant read permission only to the corresponding user.

## 5. Important ownership rule

The database document has an `ownerId` field and the Appwrite document permission should also be set to the same user.

The adapter relies on Appwrite permissions to prevent another user from reading a document/file.

## 6. Frontend

Open `frontend/index.html` through a local web server, not `file://`:

```bash
cd frontend
python -m http.server 5500
```

Select Appwrite mode and enter:

- Endpoint
- Project ID
- Database ID
- Files collection ID
- Storage bucket ID

## 7. Seeding

The Node seed script uses an Appwrite API key. Put the key only in a local `.env` file under `appwrite/`.

Never commit the key.

```bash
cd appwrite
npm install
node seed-appwrite.js
```

The script creates Alice, Bob, and Carol and creates two files per user.
