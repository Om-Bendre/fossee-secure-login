(function () {
  const originalFetch = window.fetch.bind(window);

  function appwriteMode() {
    return document.querySelector('input[name="backendMode"]:checked')?.value === "appwrite";
  }

  function config() {
    return {
      endpoint: document.getElementById("awEndpoint").value,
      projectId: document.getElementById("awProjectId").value,
      databaseId: document.getElementById("awDatabaseId").value,
      collectionId: document.getElementById("awFilesCollectionId").value,
      bucketId: document.getElementById("awBucketId").value
    };
  }

  function services() {
    const c = config();
    if (!window.Appwrite) throw new Error("Appwrite Web SDK is not loaded.");
    const client = new Appwrite.Client()
      .setEndpoint(c.endpoint)
      .setProject(c.projectId);
    return {
      config: c,
      account: new Appwrite.Account(client),
      databases: new Appwrite.Databases(client),
      storage: new Appwrite.Storage(client)
    };
  }

  function jsonResponse(body, status) {
    return new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" }
    });
  }

  async function appwriteFetch(url, options = {}) {
    const parsed = new URL(url, window.location.href);
    const path = parsed.pathname;
    const method = (options.method || "GET").toUpperCase();
    const body = options.body ? JSON.parse(options.body) : {};
    const { config: c, account, databases, storage } = services();

    try {
      if (path.endsWith("/register") && method === "POST") {
        const user = await account.create({
          userId: Appwrite.ID.unique(),
          email: body.email,
          password: body.password
        });
        return jsonResponse({ id: user.$id, email: user.email }, 201);
      }

      if (path.endsWith("/login") && method === "POST") {
        const session = await account.createEmailPasswordSession({
          email: body.email,
          password: body.password
        });
        const user = await account.get();
        return jsonResponse({
          token: session.$id,
          user: { id: user.$id, email: user.email }
        }, 200);
      }

      if (path.endsWith("/logout") && method === "POST") {
        await account.deleteSession({ sessionId: "current" });
        return jsonResponse({ message: "Logout successful" }, 200);
      }

      if (path.endsWith("/me") && method === "GET") {
        const user = await account.get();
        return jsonResponse({
          id: user.$id,
          email: user.email,
          profile: {
            fullName: user.name || "",
            displayName: user.name || "",
            bio: "",
            role: "user"
          }
        }, 200);
      }

      if (path.endsWith("/files") && method === "GET") {
        const result = await databases.listDocuments({
          databaseId: c.databaseId,
          collectionId: c.collectionId
        });
        return jsonResponse(result.documents.map(d => ({
          id: d.$id,
          ownerId: d.ownerId,
          fileName: d.fileName,
          mimeType: d.mimeType,
          sizeBytes: d.sizeBytes || 0,
          uploadedAt: d.uploadedAt || d.$createdAt
        })), 200);
      }

      const match = path.match(/\/files\/([^/]+)(\/download)?$/);
      if (match && method === "GET") {
        const document = await databases.getDocument({
          databaseId: c.databaseId,
          collectionId: c.collectionId,
          documentId: match[1]
        });

        if (match[2]) {
          const url = storage.getFileDownload({
            bucketId: c.bucketId,
            fileId: document.storageFileId
          });
          return originalFetch(url.toString());
        }

        return jsonResponse({
          id: document.$id,
          ownerId: document.ownerId,
          fileName: document.fileName,
          mimeType: document.mimeType,
          sizeBytes: document.sizeBytes || 0,
          uploadedAt: document.uploadedAt || document.$createdAt
        }, 200);
      }

      return jsonResponse({ detail: "Not found" }, 404);
    } catch (error) {
      return jsonResponse({
        detail: error.message || "Appwrite request failed"
      }, error.code || 500);
    }
  }

  window.fetch = function (url, options) {
    if (appwriteMode()) {
      return appwriteFetch(url, options);
    }
    return originalFetch(url, options);
  };
})();
