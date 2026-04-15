// Common Types
export type Pagination = {
  page: number;
  perPage: number;
  total: number;
};

// Request Types
export type RequestStatus = 
  | "pending"   // در انتظار پردازش
  | "processing" // در حال پردازش
  | "completed" // تکمیل شده
  | "failed";   // خطا در پردازش

export type Request = {
  id: string;
  query: string;
  status: RequestStatus;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  error?: string;
  metadata?: Record<string, unknown>;
};

export type RequestStats = {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  avgProcessingTime: number; // میانگین زمان پردازش (ثانیه)
};

// Query Types
export type QueryStatus = 
  | "queued"     // در صف
  | "running"    // در حال اجرا
  | "completed"  // تکمیل شده
  | "failed";    // خطا

export type Query = {
  id: string;
  requestId: string;
  elasticsearchQuery: string;
  status: QueryStatus;
  startedAt?: string;
  completedAt?: string;
  error?: string;
  resultCount?: number;
};

export type QueryStats = {
  total: number;
  queued: number;
  running: number;
  completed: number;
  failed: number;
  avgExecutionTime: number; // میانگین زمان اجرا (ثانیه)
};

// Result Types
export type ResultStatus = 
  | "pending"   // در انتظار export
  | "exporting" // در حال export
  | "exported"  // export شده
  | "failed";   // خطا در export

export type Result = {
  id: string;
  queryId: string;
  status: ResultStatus;
  createdAt: string;
  exportedAt?: string;
  error?: string;
  fileSize?: number;
  recordCount?: number;
};

// System Types
export type ServiceStatus = 
  | "healthy"    // سالم
  | "degraded"   // با مشکل
  | "unhealthy"; // ناسالم

export type SystemHealth = {
  elasticsearch: ServiceStatus;
  redis: ServiceStatus;
  postgres: ServiceStatus;
  celeryWorkers: ServiceStatus;
};

export type SystemStats = {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  elasticsearchStats: {
    documentsCount: number;
    diskUsage: number;
    queryLatency: number;
  };
  redisStats: {
    connectedClients: number;
    usedMemory: number;
    commandsProcessed: number;
  };
};

export type LogLevel = "info" | "warning" | "error";

export type LogEntry = {
  id: string;
  timestamp: string;
  level: LogLevel;
  service: string;
  message: string;
  metadata?: Record<string, unknown>;
};