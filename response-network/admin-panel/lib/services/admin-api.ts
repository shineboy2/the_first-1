import api from "@/app/(auth)/api";

// ============================================================================
// Type Definitions
// ============================================================================

export interface User {
  id: string;
  username: string;
  email: string;
  role: "admin" | "user";
  profile_type?: string;
  is_active: boolean;
  is_superuser?: boolean;
  full_name?: string;
  created_at: string;
  last_login: string | null;
}

export interface UserRequestAccess {
  user_id: string;
  request_type_id: string;
  max_requests_per_hour: number;
  is_active: boolean;
  created_at: string;
}

export interface ProfileType {
  name: string;
  display_name: string;
  description: string | null;
  daily_request_limit: number;
  monthly_request_limit: number;
  max_results_per_request: number;
  is_active: boolean;
  is_builtin: boolean;
  permissions?: Record<string, any>;
}

export interface ExportStatus {
  task_id: string;
  state: string;
  result?: unknown;
  error?: string;
}

export interface HealthStatus {
  status: "ok" | "warning" | "error";
  services: {
    database: string;
    redis: string;
  };
}

export interface SystemStats {
  users: {
    total: number;
    active: number;
  };
  requests: {
    total: number;
    processing: number;
    completed: number;
    failed: number;
  };
  database: {
    size: string;
  };
  results: {
    total: number;
  };
  requests_by_type?: { type: string; count: number }[];
  user_request_stats?: { username: string; total: number; completed: number }[];
  request_types_stats?: { active: number; inactive: number };
}

export interface CacheStats {
  keys: number;
  size?: number; // Optional for backward compatibility
  memory_usage: string;
  keyspace_hits: number;
  keyspace_misses: number;
  hit_ratio: string;
  clients: {
    connected_clients: number;
  };
}

export interface Request {
  id: string;
  original_request_id?: string;
  user_id: string;
  username?: string;
  request_type?: string; // mapped from query_type
  query_type?: string;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
  updated_at: string;
  query_params?: Record<string, unknown>;
  content?: Record<string, unknown>;
  result?: Record<string, unknown> | null;
  error?: string | null;
}

export interface RequestType {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  is_public: boolean;
  version: string;
  max_items_per_request: number;
  available_indices: string[];
  elasticsearch_query_template: Record<string, unknown> | null;
  parameters?: Array<{
    name: string;
    description?: string;
    parameter_type: string;
    is_required: boolean;
    validation_rules?: string;
    placeholder_key?: string;
  }>;
  created_at: string;
  created_by_id: string;
}

export interface ProfileTypeAccess {
  id: string;
  profile_type_id: string;
  request_type_id: string;
  profile_type_name?: string;
  max_requests_per_day: number | null;
  max_requests_per_month: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExternalAPI {
  id: string;
  name: string;
  description: string | null;
  endpoint_url: string;
  http_method: string;
  is_active: boolean;
  auth_type: string;
  auth_config: Record<string, any> | null;
  static_headers: Record<string, any> | null;
  payload_template: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface ElasticsearchConfig {
  id: string;
  url: string;
  username?: string;
  verify_ssl: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ElasticsearchConfigCreate {
  url: string;
  username?: string;
  password?: string;
  verify_ssl?: boolean;
  is_active?: boolean;
}

export interface ElasticsearchConfigUpdate {
  url?: string;
  username?: string;
  password?: string;
  verify_ssl?: boolean;
  is_active?: boolean;
}

// ============================================================================
// Health Service
// ============================================================================

export const healthService = {
  async getHealth(): Promise<HealthStatus> {
    const response = await api.get("/api/v1/system/health");
    return response.data;
  },
};

// ============================================================================
// Stats Service
// ============================================================================

export const statsService = {
  async getSystemStats(): Promise<SystemStats> {
    const response = await api.get("/api/v1/monitoring/stats");
    return response.data;
  },

  async getCacheStats(): Promise<CacheStats> {
    const response = await api.get("/api/v1/monitoring/cache-stats");
    return response.data;
  },

  async getRequestStats() {
    const response = await api.get("/api/v1/monitoring/request-stats");
    return response.data;
  },
};

// ============================================================================
// User Service
// ============================================================================

export const userService = {
  async getUsers(): Promise<User[]> {
    try {
      const response = await api.get("/api/v1/users");
      const users = Array.isArray(response.data) ? response.data : (response.data?.users || []);

      if (!Array.isArray(users)) {
        console.warn("getUsers: Expected array but got", users);
        return [];
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return users.map((u: any) => ({
        ...u,
        role: u.role || (u.profile_type === 'admin' ? 'admin' : 'user')
      }));
    } catch (error) {
      console.error("Failed to fetch users:", error);
      return [];
    }
  },

  async getUserById(id: string): Promise<User> {
    const response = await api.get(`/api/v1/users/${id}`);
    const user = response.data;
    return {
      ...user,
      role: user.role || (user.profile_type === 'admin' ? 'admin' : 'user')
    };
  },


  async createUser(data: unknown): Promise<User> {
    const response = await api.post("/api/v1/users", data);
    return response.data;
  },

  async updateUser(id: string, data: unknown): Promise<User> {
    const response = await api.put(`/api/v1/users/${id}`, data);
    return response.data;
  },

  async deleteUser(id: string): Promise<void> {
    await api.delete(`/api/v1/users/${id}`);
  },


  async activateUser(id: string): Promise<unknown> {
    const response = await api.post(`/api/v1/users/${id}/activate`);
    return response.data;
  },

  async deactivateUser(id: string): Promise<unknown> {
    const response = await api.post(`/api/v1/users/${id}/suspend`);
    return response.data;
  },

  // Request Access Management
  async getUserRequestAccess(userId: string): Promise<UserRequestAccess[]> {
    const response = await api.get(`/api/v1/users/${userId}/request-access`);
    return response.data;
  },

  async grantRequestAccess(userId: string, data: Array<{ request_type_id: string; max_requests_per_hour: number; is_active: boolean }>): Promise<UserRequestAccess[]> {
    const response = await api.post(`/api/v1/users/${userId}/request-access`, data);
    return response.data;
  },

  async revokeRequestAccess(userId: string, requestTypeId: string): Promise<void> {
    await api.delete(`/api/v1/users/${userId}/request-access/${requestTypeId}`);
  },

  // Password Management
  async resetPassword(userId: string, newPassword: string): Promise<unknown> {
    const response = await api.post(`/api/v1/users/${userId}/reset-password`, { new_password: newPassword });
    return response.data;
  },

  async changePassword(data: { current_password: string; new_password: string }): Promise<unknown> {
    const response = await api.post("/api/v1/users/change-password", data);
    return response.data;
  },

  // Export
  async exportUsers(): Promise<{ task_id: string; status: string; message: string }> {
    const response = await api.post("/api/v1/users/export/now");
    return response.data;
  },

  async getExportStatus(taskId: string): Promise<ExportStatus> {
    const response = await api.get(`/api/v1/users/export/status/${taskId}`);
    return response.data;
  },
};

// ============================================================================
// Profile Type Service
// ============================================================================

export const profileTypeService = {
  async getProfileTypes(): Promise<ProfileType[]> {
    const response = await api.get("/api/v1/profile-types");
    return response.data;
  },

  async getProfileType(name: string): Promise<ProfileType> {
    const response = await api.get(`/api/v1/profile-types/${name}`);
    return response.data;
  },

  async createProfileType(data: unknown): Promise<ProfileType> {
    const response = await api.post("/api/v1/profile-types", data);
    return response.data;
  },

  async updateProfileType(name: string, data: unknown): Promise<ProfileType> {
    const response = await api.put(`/api/v1/profile-types/${name}`, data);
    return response.data;
  },

  async deleteProfileType(name: string): Promise<void> {
    const response = await api.delete(`/api/v1/profile-types/${name}`);
    return response.data;
  },
};

// ============================================================================
// Request Service
// ============================================================================

export const requestService = {
  async getRecentRequests(limit: number = 10): Promise<Request[]> {
    const response = await api.get(`/api/v1/requests?limit=${limit}`);
    return response.data.requests || [];
  },



  async retryAllFailed(): Promise<any> {
    const response = await api.post("/api/v1/requests/retry-all");
    return response.data;
  },

  async getRequestById(id: string): Promise<Request> {
    const response = await api.get(`/api/v1/requests/${id}`);
    return response.data;
  },

  async getRequestsByStatus(
    status: "pending" | "processing" | "completed" | "failed"
  ): Promise<Request[]> {
    const response = await api.get(`/api/v1/requests?status=${status}`);
    return response.data.requests || [];
  },

  async createRequest(data: {
    request_type: string;
    payload?: Record<string, unknown>;
  }): Promise<Request> {
    const response = await api.post("/api/v1/requests", data);
    return response.data;
  },

  async cancelRequest(id: string): Promise<void> {
    await api.post(`/api/v1/requests/${id}/cancel`);
  },

  async retryRequest(id: string): Promise<Request> {
    const response = await api.post(`/api/v1/requests/${id}/retry`);
    return response.data;
  },

  async getRequestTypes(): Promise<RequestType[]> {
    const response = await api.get("/api/v1/request-types/");
    return response.data;
  },

  async getRequestType(id: string): Promise<RequestType> {
    const response = await api.get(`/api/v1/request-types/${id}`);
    return response.data;
  },

  async createRequestType(data: { name: string; description?: string; is_active?: boolean }): Promise<RequestType> {
    const response = await api.post("/api/v1/request-types/", data);
    return response.data;
  },

  async updateRequestType(id: string, data: unknown): Promise<RequestType> {
    const response = await api.put(`/api/v1/request-types/${id}`, data);
    return response.data;
  },

  async configureRequestTypeParams(id: string, data: unknown): Promise<RequestType> {
    const response = await api.put(`/api/v1/request-types/${id}/configure`, data);
    return response.data;
  },

  async configureRequestTypeQuery(id: string, data: { elasticsearch_query_template: string }): Promise<RequestType> {
    const response = await api.put(`/api/v1/request-types/${id}/query`, data);
    return response.data;
  },

  async deleteRequestType(id: string): Promise<void> {
    await api.delete(`/api/v1/request-types/${id}`);
  },

  async getRequestTypeAccess(id: string): Promise<Array<{
    user_id: string;
    username: string;
    email: string;
    max_requests_per_hour: number;
    is_active: boolean;
  }>> {
    const response = await api.get(`/api/v1/request-types/${id}/access`);
    return response.data;
  },

  // Request Type Access Management
  async grantRequestTypeAccess(requestTypeId: string, data: { user_ids: string[]; max_requests_per_hour: number; is_active: boolean }): Promise<UserRequestAccess[]> {
    const response = await api.post(`/api/v1/request-types/${requestTypeId}/access`, data);
    return response.data;
  },

  async listRequestTypeAccess(requestTypeId: string): Promise<UserRequestAccess[]> {
    const response = await api.get(`/api/v1/request-types/${requestTypeId}/access`);
    return response.data;
  },

  async revokeRequestTypeAccess(requestTypeId: string, userId: string): Promise<void> {
    await api.delete(`/api/v1/request-types/${requestTypeId}/access/${userId}`);
  },

  // Profile Type Access Management
  async getProfileTypeAccess(requestTypeId: string): Promise<ProfileTypeAccess[]> {
    const response = await api.get(`/api/v1/request-types/${requestTypeId}/profile-access`);
    return response.data;
  },

  async grantProfileTypeAccess(
    requestTypeId: string,
    data: { profile_type_ids: string[]; max_requests_per_day?: number; max_requests_per_month?: number; is_active: boolean }
  ): Promise<ProfileTypeAccess[]> {
    const response = await api.post(`/api/v1/request-types/${requestTypeId}/profile-access`, data);
    return response.data;
  },

  async updateProfileTypeAccess(
    requestTypeId: string,
    profileTypeId: string,
    data: { max_requests_per_day?: number; max_requests_per_month?: number; is_active?: boolean }
  ): Promise<ProfileTypeAccess> {
    const response = await api.put(`/api/v1/request-types/${requestTypeId}/profile-access/${profileTypeId}`, data);
    return response.data;
  },

  async revokeProfileTypeAccess(requestTypeId: string, profileTypeId: string): Promise<void> {
    await api.delete(`/api/v1/request-types/${requestTypeId}/profile-access/${profileTypeId}`);
  },
};

// ============================================================================
// Settings Service
// ============================================================================

export const settingsService = {
  async getSettings() {
    const response = await api.get("/api/v1/settings");
    return response.data;
  },

  async updateSettings(data: Record<string, unknown>) {
    const response = await api.put("/api/v1/settings", data);
    return response.data;
  },
};

// ============================================================================
// Monitoring Service
// ============================================================================

export const monitoringService = {
  async getMetrics() {
    const response = await api.get("/api/v1/monitoring/metrics");
    return response.data;
  },

  async getLogsStats() {
    const response = await api.get("/api/v1/monitoring/logs-stats");
    return response.data;
  },

  async getSystemHealth() {
    const response = await api.get("/api/v1/monitoring/system-health");
    return response.data;
  },
};

// ============================================================================
// Worker Settings Service
// ============================================================================

export interface WorkerSettings {
  id: string;
  name: string;
  worker_type: string;
  is_active: boolean;
  storage_config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export const workerService = {
  async getWorkerSettings(): Promise<WorkerSettings[]> {
    try {
      const response = await api.get("/api/v1/worker-settings/");
      return Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      console.error("Failed to fetch worker settings:", error);
      return [];
    }
  },

  async getWorkerSetting(id: string): Promise<WorkerSettings> {
    const response = await api.get(`/api/v1/worker-settings/${id}`);
    return response.data;
  },

  async createWorkerSettings(data: any): Promise<WorkerSettings> {
    const response = await api.post("/api/v1/worker-settings/", data);
    return response.data;
  },

  async updateWorkerSettings(id: string, data: unknown): Promise<WorkerSettings> {
    const response = await api.put(`/api/v1/worker-settings/${id}`, data);
    return response.data;
  },

  async deleteWorkerSettings(id: string): Promise<void> {
    await api.delete(`/api/v1/api/v1/worker-settings/${id}`);
  },

  async toggleWorker(id: string): Promise<WorkerSettings> {
    const response = await api.post(`/api/v1/api/v1/worker-settings/${id}/toggle`);
    return response.data;
  },

  async testStorageConnection(id: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/api/v1/api/v1/worker-settings/${id}/test-connection`);
    return response.data;
  },
};

// ============================================================================
// Admin Tasks Service
// ============================================================================

export interface QueueStats {
  default_queue_length: number;
  notes: string;
}

export interface WorkerStats {
  worker_name: string;
  pool_type: string;
  max_concurrency: number;
  active_tasks: number;
  processed_tasks: number;
  offline: boolean;
}

export interface PendingTask {
  id: string;
  name: string;
  args: unknown[];
  kwargs: Record<string, unknown>;
  created_at: string;
}

export const adminTasksService = {
  async getQueueStats(): Promise<QueueStats> {
    const response = await api.get("/api/v1/admin/tasks/queue/stats");
    return response.data;
  },

  async getWorkersStats(): Promise<WorkerStats[]> {
    try {
      const response = await api.get("/api/v1/admin/tasks/workers/stats");
      return Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      console.error("Failed to fetch workers stats:", error);
      return [];
    }
  },

  async getPendingTasks(): Promise<PendingTask[]> {
    try {
      const response = await api.get("/api/v1/admin/tasks/queue/pending");
      const tasks = response.data?.tasks;

      if (!Array.isArray(tasks)) {
        console.warn("getPendingTasks: Expected array but got", tasks);
        return [];
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return tasks.map((task: any) => ({
        id: task.id || task.task_id || `unknown-${Math.random().toString(36).substr(2, 9)}`,
        name: task.name || 'Unknown Task',
        args: task.args || [],
        kwargs: task.kwargs || {},
        created_at: task.created_at || task.eta || new Date().toISOString() // fallback for created_at
      }));
    } catch (error) {
      console.error("Failed to fetch pending tasks:", error);
      return [];
    }
  },

  async skipTask(taskId: string): Promise<void> {
    await api.post(`/api/v1/admin/tasks/tasks/${taskId}/skip`);
  },

  async clearQueue(): Promise<void> {
    await api.delete("/api/v1/admin/tasks/queue/clear");
  },

  async retryTask(taskId: string): Promise<void> {
    await api.post(`/api/v1/admin/tasks/tasks/${taskId}/retry`);
  },
};

// ============================================================================
// Storage Config Service (Multiple Operation Types)
// ============================================================================

export type OperationType = 'user_export' | 'request_types_export' | 'result_export' | 'request_import';

export interface StorageConfig {
  operation_type: OperationType;
  enabled: boolean;
  format: string;
  destination_type: 'local' | 'ftp';
  local_path?: string;
  ftp_host?: string;
  ftp_port?: number;
  ftp_user?: string;
  ftp_password?: string;
  ftp_path?: string;
  ftp_use_tls?: boolean;
  schedule?: string;
  configured?: boolean;
}

export const OPERATION_LABELS: Record<OperationType, { title: string; description: string }> = {
  user_export: {
    title: "خروجی کاربران",
    description: "ارسال کاربران به Request Network"
  },
  request_types_export: {
    title: "خروجی انواع درخواست",
    description: "ارسال انواع درخواست به Request Network"
  },
  result_export: {
    title: "خروجی نتایج",
    description: "ارسال نتایج کوئری‌ها به Request Network"
  },
  request_import: {
    title: "ورودی درخواست‌ها",
    description: "دریافت درخواست‌ها از Request Network"
  }
};

export const storageConfigService = {
  // Get all storage configurations
  async getAllConfigs(): Promise<StorageConfig[]> {
    const response = await api.get("/api/v1/admin/exports/configs");
    return response.data;
  },

  // Get config for specific operation type
  async getConfig(operationType: OperationType): Promise<StorageConfig> {
    const response = await api.get(`/api/v1/admin/exports/config/${operationType}`);
    return response.data;
  },

  // Update config for specific operation type
  async updateConfig(operationType: OperationType, data: Partial<StorageConfig>): Promise<StorageConfig> {
    const response = await api.post(`/api/v1/admin/exports/config/${operationType}`, data);
    return response.data;
  },

  // Test specific operation (triggers actual export/import)
  async testOperation(operationType: OperationType): Promise<{ success: boolean; message: string; task_id?: string }> {
    const response = await api.post(`/api/v1/admin/exports/test/${operationType}`);
    return response.data;
  },

  // Test connection (FTP/Local) without triggering export
  async testConnection(operationType: OperationType): Promise<{ success: boolean; message: string; files_count?: number }> {
    const response = await api.post(`/api/v1/admin/exports/test-connection/${operationType}`);
    return response.data;
  },

  // Legacy: Get default export config (user_export)
  async getExportConfig(): Promise<StorageConfig> {
    const response = await api.get("/api/v1/admin/exports/config");
    return response.data;
  },

  // Legacy: Update default export config (user_export)
  async updateExportConfig(data: Partial<StorageConfig>): Promise<StorageConfig> {
    const response = await api.post("/api/v1/admin/exports/config", data);
    return response.data;
  },

  // Legacy: Test exports (user_export)
  async testExports(): Promise<{ success: boolean; message: string }> {
    const response = await api.post("/api/v1/admin/exports/test");
    return response.data;
  },

  async getExportStatus(): Promise<{ status: string; last_export?: string }> {
    const response = await api.get("/api/v1/admin/exports/status");
    return response.data;
  },
};

// Legacy alias for backward compatibility
export const exportConfigService = storageConfigService;

// ============================================================================
// External API Service
// ============================================================================

export const externalApiService = {
  async getExternalAPIs(): Promise<ExternalAPI[]> {
    const response = await api.get("/api/v1/external-apis/");
    return response.data;
  },

  async getExternalAPI(id: string): Promise<ExternalAPI> {
    const response = await api.get(`/api/v1/external-apis/${id}`);
    return response.data;
  },

  async createExternalAPI(data: Partial<ExternalAPI>): Promise<ExternalAPI> {
    const response = await api.post("/api/v1/external-apis/", data);
    return response.data;
  },

  async updateExternalAPI(id: string, data: Partial<ExternalAPI>): Promise<ExternalAPI> {
    const response = await api.patch(`/api/v1/external-apis/${id}`, data);
    return response.data;
  },

  async deleteExternalAPI(id: string): Promise<void> {
    await api.delete(`/api/v1/external-apis/${id}`);
  },

  async getProfileTypeAccess(profileType: string): Promise<{ allowed_external_apis: string[] }> {
    const response = await api.get(`/api/v1/external-apis/profile-types/${profileType}/access`);
    return response.data;
  },

  async updateProfileTypeAccess(profileType: string, allowedApis: string[]): Promise<void> {
    await api.patch(`/api/v1/external-apis/profile-types/${profileType}/access`, {
      allowed_external_apis: allowedApis,
    });
  },

  async grantUserAccess(apiId: string, userIds: string[]): Promise<void> {
    await api.post(`/api/v1/external-apis/${apiId}/user-access`, {
      user_ids: userIds,
    });
  },

  async getUserAccess(apiId: string): Promise<any[]> {
    const response = await api.get(`/api/v1/external-apis/${apiId}/user-access`);
    return response.data;
  },

  async revokeUserAccess(apiId: string, userId: string): Promise<void> {
    await api.delete(`/api/v1/external-apis/${apiId}/user-access/${userId}`);
  },
};

// ============================================================================
// Elasticsearch Config Service
// ============================================================================

export const elasticsearchConfigService = {
  async getActiveConfig(): Promise<ElasticsearchConfig> {
    const response = await api.get("/api/v1/admin/elasticsearch/config/active");
    return response.data;
  },

  async getConfigs(): Promise<ElasticsearchConfig[]> {
    const response = await api.get("/api/v1/admin/elasticsearch/config");
    return response.data;
  },

  async getConfig(id: string): Promise<ElasticsearchConfig> {
    const response = await api.get(`/api/v1/admin/elasticsearch/config/${id}`);
    return response.data;
  },

  async createConfig(data: ElasticsearchConfigCreate): Promise<ElasticsearchConfig> {
    const response = await api.post("/api/v1/admin/elasticsearch/config", data);
    return response.data;
  },

  async updateConfig(id: string, data: ElasticsearchConfigUpdate): Promise<ElasticsearchConfig> {
    const response = await api.put(`/api/v1/admin/elasticsearch/config/${id}`, data);
    return response.data;
  },

  async deleteConfig(id: string): Promise<void> {
    await api.delete(`/api/v1/admin/elasticsearch/config/${id}`);
  },

  async testConfig(id: string): Promise<{ success: boolean; message: string; config_id: string }> {
    const response = await api.post(`/api/v1/admin/elasticsearch/config/${id}/test`);
    return response.data;
  },

  async testNewConfig(data: ElasticsearchConfigCreate): Promise<{ success: boolean; message: string }> {
    const response = await api.post("/api/v1/admin/elasticsearch/config/test-new", data);
    return response.data;
  },
};

const adminApi = {
  healthService,
  statsService,
  userService,
  requestService,

  settingsService,
  monitoringService,
  profileTypeService,
  workerService,
  adminTasksService,
  exportConfigService,
  storageConfigService,
  externalApiService,
  elasticsearchConfigService,
};

export default adminApi;
