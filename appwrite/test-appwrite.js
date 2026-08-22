require("dotenv").config();

const sdk = require("node-appwrite");

const client = new sdk.Client()
  .setEndpoint(process.env.APPWRITE_ENDPOINT)
  .setProject(process.env.APPWRITE_PROJECT_ID)
  .setKey(process.env.APPWRITE_API_KEY);

const databases = new sdk.Databases(client);

databases
  .get({
    databaseId: process.env.APPWRITE_DATABASE_ID
  })
  .then((database) => {
    console.log("DATABASE OK:", database.$id, database.name);
  })
  .catch((error) => {
    console.error("ERROR:", error.message, error.code);
  });
