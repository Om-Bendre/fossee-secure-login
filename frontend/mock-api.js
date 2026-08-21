(function () {
  const originalFetch = window.fetch.bind(window);

  const users = {
    "alice@example.com": { id: "user-a", password: "Password123!", name: "Alice" },
    "bob@example.com": { id: "user-b", password: "Password123!", name: "Bob" },
    "carol@example.com": { id: "user-c", password: "Password123!", name: "Carol" }
  };

  const files = [
    { id: "1", ownerId: "user-a", fileName: "alice.txt", mimeType: "text/plain", sizeBytes: 50, uploadedAt: new Date().toISOString() },
    { id: "2", ownerId: "user-b", fileName: "bob.txt", mimeType: "text/plain", sizeBytes: 48, uploadedAt: new Date().toISOString() },
    { id: "3", ownerId: "user-c", fileName: "carol.txt", mimeType: "text/plain", sizeBytes: 50, uploadedAt: new Date().toISOString() }
  ];

  let currentUserId = null;

  function mockMode() {
    return document.querySelector('input[name="backendMode"]:checked')?.value === "mock";
  }

  function response(body, status) {
    return new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" }
    });
  }

  async function mockFetch(url, options = {}) {
    const path = new URL(url, window.location.href).pathname;
    const method = (options.method || "GET").toUpperCase();
    const body = options.body ? JSON.parse(options.body) : {};

    if (path.endsWith("/register") && method === "POST") {
      if (users[body.email]) return response({ detail: "Email already registered" }, 409);
      users[body.email] = { id: "user-new", password: body.password, name: body.email };
      return response({ id: "user-new", email: body.email }, 201);
    }

    if (path.endsWith("/login") && method === "POST") {
      const user = users[body.email];
      if (!user || user.password !== body.password) {
        return response({ detail: "Invalid email or password" }, 401);
      }
      currentUserId = user.id;
      return response({ token: "mock-token", user: { id: user.id, email: body.email } }, 200);
    }

    if (path.endsWith("/logout") && method === "POST") {
      currentUserId = null;
      return response({ message: "Logout successful" }, 200);
    }

    if (!currentUserId) return response({ detail: "Not authenticated" }, 401);

    if (path.endsWith("/me") && method === "GET") {
      const user = Object.values(users).find(item => item.id === currentUserId);
      const email = Object.keys(users).find(key => users[key] === user);
      return response({
        id: user.id,
        email,
        profile: { fullName: user.name, displayName: user.name, bio: "", role: "user" }
      }, 200);
    }

    if (path.endsWith("/files") && method === "GET") {
      return response(files.filter(file => file.ownerId === currentUserId), 200);
    }

    const match = path.match(/\/files\/([^/]+)(\/download)?$/);
    if (match && method === "GET") {
      const file = files.find(item => item.id === match[1]);
      if (!file) return response({ detail: "File not found" }, 404);
      if (file.ownerId !== currentUserId) return response({ detail: "You do not have access to this file" }, 403);
      if (match[2]) {
        return new Response(`Mock bytes for ${file.fileName}`, {
          status: 200,
          headers: { "Content-Type": file.mimeType }
        });
      }
      return response(file, 200);
    }

    return response({ detail: "Not found" }, 404);
  }

  window.fetch = function (url, options) {
    if (mockMode()) return mockFetch(url, options);
    return originalFetch(url, options);
  };
})();
