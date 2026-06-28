import re

with open("lib/services/admin-api.ts", "r") as f:
    content = f.read()

# Add apiKeyService definition
api_key_code = """
export const apiKeyService = {
  async getUserApiKeys(userId: string): Promise<any[]> {
    try {
      const response = await api.get(`/api/v1/users/${userId}/api-keys`);
      return response.data || [];
    } catch (error) {
      console.error("Error fetching user API keys:", error);
      return [];
    }
  },
  async createUserApiKey(userId: string, name: string, scopes: string[] = ["read", "write"]): Promise<any> {
    const response = await api.post(`/api/v1/users/${userId}/api-keys`, { name, scopes });
    return response.data;
  },
  async revokeUserApiKey(userId: string, keyId: string): Promise<void> {
    await api.delete(`/api/v1/users/${userId}/api-keys/${keyId}`);
  }
};

export const rateLimitService = {
  async getUserRateLimits(userId: string): Promise<any> {
    return { "limit": 100, "used": 0 };
  }
};
"""

# Insert before "const adminApi = {"
if "const adminApi = {" in content:
    content = content.replace("const adminApi = {", api_key_code + "\nconst adminApi = {")
    
with open("lib/services/admin-api.ts", "w") as f:
    f.write(content)
