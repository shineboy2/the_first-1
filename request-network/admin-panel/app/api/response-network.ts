import axios from 'axios';
import { 
  Request, RequestStats, 
  Query, QueryStats,
  Result,
  SystemHealth, SystemStats, LogEntry,
  Pagination
} from '@/app/types/models';

// Create an axios instance for response network API
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_RESPONSE_API_URL || 'http://localhost:8001',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request Management
export async function getRequests(page = 1, perPage = 10) {
  const response = await api.get<{ data: Request[], pagination: Pagination }>(
    `/requests?page=${page}&per_page=${perPage}`
  );
  return response.data;
}

export async function getRequest(id: string) {
  const response = await api.get<Request>(`/requests/${id}`);
  return response.data;
}

export async function getRequestStats() {
  const response = await api.get<RequestStats>('/requests/stats');
  return response.data;
}

// Query Management
export async function getQueries(page = 1, perPage = 10) {
  const response = await api.get<{ data: Query[], pagination: Pagination }>(
    `/queries?page=${page}&per_page=${perPage}`
  );
  return response.data;
}

export async function getQuery(id: string) {
  const response = await api.get<Query>(`/queries/${id}`);
  return response.data;
}

export async function getQueryStats() {
  const response = await api.get<QueryStats>('/queries/stats');
  return response.data;
}

// Result Management
export async function getResults(page = 1, perPage = 10) {
  const response = await api.get<{ data: Result[], pagination: Pagination }>(
    `/results?page=${page}&per_page=${perPage}`
  );
  return response.data;
}

export async function getResult(id: string) {
  const response = await api.get<Result>(`/results/${id}`);
  return response.data;
}

export async function exportResult(id: string) {
  const response = await api.post<{ message: string }>(`/results/${id}/export`);
  return response.data;
}

// System Monitoring
export async function getSystemHealth() {
  const response = await api.get<SystemHealth>('/system/health');
  return response.data;
}

export async function getSystemStats() {
  const response = await api.get<SystemStats>('/system/stats');
  return response.data;
}

export async function getSystemLogs(
  page = 1, 
  perPage = 100,
  level?: 'info' | 'warning' | 'error',
  service?: string,
  startDate?: string,
  endDate?: string
) {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: perPage.toString(),
    ...(level && { level }),
    ...(service && { service }),
    ...(startDate && { start_date: startDate }),
    ...(endDate && { end_date: endDate })
  });

  const response = await api.get<{ data: LogEntry[], pagination: Pagination }>(
    `/system/logs?${params}`
  );
  return response.data;
}