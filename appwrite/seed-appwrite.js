require("dotenv").config();
const sdk = require("node-appwrite");

const endpoint = process.env.APPWRITE_ENDPOINT;
const projectId = process.env.APPWRITE_PROJECT_ID;
const apiKey = process.env.APPWRITE_API_KEY;
const databaseId = process.env.APPWRITE_DATABASE_ID;
const collectionId = process.env.APPWRITE_FILES_COLLECTION_ID;
const bucketId = process.env.APPWRITE_BUCKET_ID;

if (!endpoint || !projectId || !apiKey || !databaseId || !collectionId || !bucketId) {
  throw new Error("Missing Appwrite seed environment variables.");
}

const client = new sdk.Client()
  .setEndpoint(endpoint)
  .setProject(projectId)
  .setKey(apiKey);

const users = new sdk.Users(client);
const databases = new sdk.Databases(client);
const storage = new sdk.Storage(client);

const seedUsers = [
  ["alice-appwrite", "alice@example.com", "Password123!", "Alice"],
  ["bob-appwrite", "bob@example.com", "Password123!", "Bob"],
  ["carol-appwrite", "carol@example.com", "Password123!", "Carol"]
];

async function getOrCreateUser(id, email, password, name) {
  try {
    return await users.get({ userId: id });
  } catch (error) {
    return users.create({
      userId: id,
      email,
      password,
      name
    });
  }
}

async function main() {
  for (const [id, email, password, name] of seedUsers) {
    const user = await getOrCreateUser(id, email, password, name);

    for (let number = 1; number <= 2; number++) {
      const fileId = `${id}-file-${number}`;
      const fileName = `${name.toLowerCase()}-${number}.txt`;
      const permissions = [
        sdk.Permission.read(sdk.Role.user(user.$id))
      ];

      try {
        await storage.getFile({ bucketId, fileId });
      } catch (error) {
        const input = sdk.InputFile.fromBuffer(
          Buffer.from(`FOSSEE Appwrite demo file ${number} belonging to ${name}.\n`),
          fileName
        );
        await storage.createFile({
          bucketId,
          fileId,
          file: input,
          permissions
        });
      }

      try {
        await databases.getDocument({ databaseId, collectionId, documentId: fileId });
      } catch (error) {
        await databases.createDocument({
          databaseId,
          collectionId,
          documentId: fileId,
          data: {
            ownerId: user.$id,
            fileName,
            mimeType: "text/plain",
            sizeBytes: Buffer.byteLength(`FOSSEE Appwrite demo file ${number} belonging to ${name}.\n`),
            storageFileId: fileId,
            uploadedAt: new Date().toISOString()
          },
          permissions
        });
      }
    }
  }

  console.log("Appwrite seed complete.");
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});
