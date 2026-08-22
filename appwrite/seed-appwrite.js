require("dotenv").config();

const fs = require("fs");
const path = require("path");

const sdk = require("node-appwrite");
const { InputFile } = require("node-appwrite/file");

const endpoint = process.env.APPWRITE_ENDPOINT;
const projectId = process.env.APPWRITE_PROJECT_ID;
const apiKey = process.env.APPWRITE_API_KEY;
const databaseId = process.env.APPWRITE_DATABASE_ID;
const collectionId = process.env.APPWRITE_FILES_COLLECTION_ID;
const bucketId = process.env.APPWRITE_BUCKET_ID;

if (
  !endpoint ||
  !projectId ||
  !apiKey ||
  !databaseId ||
  !collectionId ||
  !bucketId
) {
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
    return await users.get({
      userId: id
    });
  } catch (error) {
    return await users.create({
      userId: id,
      email,
      password,
      name
    });
  }
}

async function main() {
  for (const [id, email, password, name] of seedUsers) {
    const user = await getOrCreateUser(
      id,
      email,
      password,
      name
    );

    console.log(`Processing ${name} (${email})`);

    for (let number = 1; number <= 2; number++) {
      const fileId = `${id}-file-${number}`;
      const fileName = `${name.toLowerCase()}-${number}.txt`;

      const content =
        `FOSSEE Appwrite demo file ${number} belonging to ${name}.\n`;

      const permissions = [
        sdk.Permission.read(
          sdk.Role.user(user.$id)
        )
      ];

      /*
       * ----------------------------------------
       * Create temporary local file
       * ----------------------------------------
       */

      const tempPath = path.join(
        __dirname,
        `.seed-${fileName}`
      );

      fs.writeFileSync(tempPath, content);

      /*
       * ----------------------------------------
       * Create Appwrite Storage file
       * ----------------------------------------
       */

      try {
        await storage.getFile({
          bucketId,
          fileId
        });

        console.log(`  Storage file exists: ${fileName}`);
      } catch (error) {
        const inputFile = InputFile.fromPath(
          tempPath,
          fileName
        );

        await storage.createFile({
          bucketId,
          fileId,
          file: inputFile,
          permissions
        });

        console.log(`  Created storage file: ${fileName}`);
      }

      /*
       * ----------------------------------------
       * Create Appwrite database document
       * ----------------------------------------
       */

      try {
        await databases.getDocument({
          databaseId,
          collectionId,
          documentId: fileId
        });

        console.log(`  Database document exists: ${fileId}`);
      } catch (error) {
        await databases.createDocument({
          databaseId,
          collectionId,
          documentId: fileId,
          data: {
            ownerId: user.$id,
            fileName,
            mimeType: "text/plain",
            sizeBytes: Buffer.byteLength(content),
            storageFileId: fileId,
            uploadedAt: new Date().toISOString()
          },
          permissions
        });

        console.log(`  Created database document: ${fileId}`);
      }

      /*
       * ----------------------------------------
       * Remove temporary local file
       * ----------------------------------------
       */

      if (fs.existsSync(tempPath)) {
        fs.unlinkSync(tempPath);
      }
    }
  }

  console.log("\nAppwrite seed complete.");
}

main().catch((error) => {
  console.error("\nAppwrite seed failed:");
  console.error(error);
  process.exit(1);
});