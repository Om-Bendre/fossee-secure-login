require("dotenv").config();

const sdk = require("node-appwrite");

const client = new sdk.Client()
  .setEndpoint(process.env.APPWRITE_ENDPOINT)
  .setProject(process.env.APPWRITE_PROJECT_ID)
  .setKey(process.env.APPWRITE_API_KEY);

const databases = new sdk.Databases(client);

databases
  .listDocuments({
    databaseId: process.env.APPWRITE_DATABASE_ID,
    collectionId: process.env.APPWRITE_FILES_COLLECTION_ID
  })
  .then((result) => {
    console.log("FILES RESOURCE OK");
    console.log("Count:", result.total);
  })
  .catch((error) => {
    console.error("ERROR:", error.message, error.code);
  });
