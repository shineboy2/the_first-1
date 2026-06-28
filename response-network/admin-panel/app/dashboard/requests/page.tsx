"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth-store";
import { requestService } from "@/lib/services/admin-api";
import type { Request } from "@/lib/services/admin-api";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, AlertCircle, RefreshCw, Search } from "lucide-react";

interface RequestsState {
  requests: Request[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  statusFilter: "all" | "pending" | "processing" | "completed" | "failed";
}

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Eye } from "lucide-react";

export default function RequestsPage() {
  const router = useRouter();
  const { user: currentUser, isLoading: authLoading } = useAuthStore();
  const [selectedRequest, setSelectedRequest] = useState<Request | null>(null);
  const [state, setState] = useState<RequestsState>({
    requests: [],
    loading: true,
    error: null,
    searchTerm: "",
    statusFilter: "all",
  });

  // Fetch requests
  useEffect(() => {
    const fetchRequests = async () => {
      try {
        setState((prev) => ({ ...prev, loading: true, error: null }));
        const data = await requestService.getRecentRequests();
        setState((prev) => ({
          ...prev,
          requests: data,
          loading: false,
        }));
      } catch (error) {
        console.error("Error fetching requests:", error);
        setState((prev) => ({
          ...prev,
          loading: false,
          error: "خطا در دریافت لیست درخواست‌ها",
        }));
      }
    };

    if (!authLoading) {
      fetchRequests();
    }
  }, [authLoading]);

  // Filter requests
  const filteredRequests = state.requests.filter((req) => {
    const matchesSearch =
      req.id.includes(state.searchTerm) ||
      req.user_id.includes(state.searchTerm);
    const matchesStatus =
      state.statusFilter === "all" || req.status === state.statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleRetry = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      if (!confirm("آیا مطمئن هستید که می‌خواهید مجدداً تلاش کنید؟")) return;

      await requestService.retryRequest(id);
      handleRefresh(); // Reload list
    } catch {
      alert("خطا در ارسال درخواست تلاش مجدد");
    }
  };

  const handleRetryAll = async () => {
    try {
      if (!confirm("آیا مطمئن هستید که می‌خواهید همه درخواست‌های ناموفق را مجدداً تلاش کنید؟")) return;

      setState((prev) => ({ ...prev, loading: true }));
      const result = await requestService.retryAllFailed();
      alert(result.message);
      handleRefresh();
    } catch {
      setState((prev) => ({ ...prev, loading: false }));
      alert("خطا در تلاش مجدد همه درخواست‌ها");
    }
  };

  const handleRefresh = async () => {
    try {
      setState((prev) => ({ ...prev, loading: true }));
      const data = await requestService.getRecentRequests();
      setState((prev) => ({
        ...prev,
        requests: Array.isArray(data) ? data : [],
        loading: false,
      }));
    } catch {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: "خطا در تازه‌سازی اطلاعات",
      }));
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    const normalized = status.toLowerCase();
    if (normalized === "completed_success") return "default";
    if (normalized === "completed_error") return "secondary";
    if (normalized === "completed") return "default";
    if (normalized === "failed") return "destructive";
    if (normalized === "processing") return "secondary";
    return "outline";
  };

  const getStatusLabel = (status: string) => {
    const normalized = status.toLowerCase();
    if (normalized === "completed_success") return "موفق ✓";
    if (normalized === "completed_error") return "تکمیل شده (خطا)";
    if (normalized === "completed") return "کامل شده";
    if (normalized === "processing") return "درحال پردازش";
    if (normalized === "failed") return "ناموفق";
    if (normalized === "pending") return "درانتظار";
    return status;
  };

  // Check auth
  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!currentUser) {
    router.push("/login");
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="border-b bg-white dark:bg-gray-800">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                درخواست‌ها
              </h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                نظارت و مدیریت درخواست‌های سیستم
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={state.loading}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
            {state.requests.some(r => r.status === 'failed') && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleRetryAll}
                disabled={state.loading}
                className="ml-2"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                تلاش مجدد همه
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Error Alert */}
        {state.error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>خطا</AlertTitle>
            <AlertDescription>{state.error}</AlertDescription>
          </Alert>
        )}

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-5 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">کل درخواست‌ها</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{state.requests.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">در انتظار</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-yellow-600">
                {state.requests.filter((r) => r.status === "pending").length}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">موفق</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">
                {state.requests.filter((r) => (r as any).effective_status?.toLowerCase?.() === "completed_success" || (r.status === "completed" && !(r as any).has_error)).length}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">خطا دار</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-600">
                {state.requests.filter((r) => (r as any).effective_status?.toLowerCase?.() === "completed_error" || ((r as any).has_error && r.status === "completed")).length}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">ناموفق</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-600">
                {state.requests.filter((r) => r.status === "failed").length}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Filter */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>جستجو و فیلتر</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2 flex-col sm:flex-row">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <Input
                  placeholder="جستجو بر اساس ID یا کاربر"
                  value={state.searchTerm}
                  onChange={(e) =>
                    setState((prev) => ({ ...prev, searchTerm: e.target.value }))
                  }
                  className="pl-10"
                />
              </div>

              <div className="flex gap-1 flex-wrap">
                {(["all", "pending", "processing", "completed", "failed"] as const).map(
                  (status) => (
                    <Button
                      key={status}
                      variant={state.statusFilter === status ? "default" : "outline"}
                      size="sm"
                      onClick={() =>
                        setState((prev) => ({
                          ...prev,
                          statusFilter: status,
                        }))
                      }
                    >
                      {status === "all" && "همه"}
                      {status === "pending" && "در انتظار"}
                      {status === "processing" && "پردازش"}
                      {status === "completed" && "تکمیل"}
                      {status === "failed" && "ناموفق"}
                    </Button>
                  )
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Requests Table */}
        <Card>
          <CardHeader>
            <CardTitle>لیست درخواست‌ها</CardTitle>
            <CardDescription>{filteredRequests.length} درخواست</CardDescription>
          </CardHeader>
          <CardContent>
            {state.loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID درخواست</TableHead>
                      <TableHead>کاربر</TableHead>
                      <TableHead>وضعیت</TableHead>
                      <TableHead>تاریخ ایجاد</TableHead>
                      <TableHead>آخرین به‌روز رسانی</TableHead>
                      <TableHead>عملیات</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredRequests.length > 0 ? (
                      filteredRequests.map((request) => (
                        <TableRow key={request.id}>
                          <TableCell className="font-mono text-sm">
                            {request.id.substring(0, 8)}...
                          </TableCell>
                          <TableCell>
                            <div className="flex flex-col">
                              <span className="font-medium text-sm">{request.username || "Unknown"}</span>
                              <span className="text-xs text-gray-400">{request.user_id.substring(0, 8)}...</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-2 items-center">
                              <Badge variant={getStatusBadgeVariant((request as any).effective_status || request.status)}>
                                {getStatusLabel((request as any).effective_status || request.status)}
                              </Badge>
                              {(request as any).is_external_api && (
                                <Badge variant="secondary" className="bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                                  API: {(request as any).api_name || 'External'}
                                </Badge>
                              )}
                              {!(request as any).is_external_api && request.query_type === 'elasticsearch' && (
                                <Badge variant="outline" className="bg-blue-50 text-blue-700 dark:bg-blue-900 dark:text-blue-200">
                                  Elasticsearch
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="text-sm text-gray-600 dark:text-gray-400">
                            {new Date(request.created_at).toLocaleDateString("fa-IR", {
                              year: "numeric",
                              month: "2-digit",
                              day: "2-digit",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </TableCell>
                          <TableCell className="text-sm text-gray-600 dark:text-gray-400">
                            {new Date(request.updated_at).toLocaleDateString("fa-IR", {
                              year: "numeric",
                              month: "2-digit",
                              day: "2-digit",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setSelectedRequest(request)}
                            >
                              <Eye className="h-4 w-4 ml-1" />
                              مشاهده
                            </Button>
                            {request.status === 'failed' && (
                              <Button
                                variant="outline"
                                size="sm"
                                className="mr-2 text-red-500 hover:text-red-700 hover:bg-red-50"
                                onClick={(e) => handleRetry(request.id, e)}
                              >
                                <RefreshCw className="h-4 w-4 ml-1" />
                                تلاش مجدد
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8">
                          <p className="text-gray-500 dark:text-gray-400">
                            درخواستی یافت نشد
                          </p>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Details Dialog */}
      <Dialog open={!!selectedRequest} onOpenChange={(open) => !open && setSelectedRequest(null)}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>جزئیات درخواست {selectedRequest?.id.substring(0, 8)}</DialogTitle>
            <DialogDescription>
              اطلاعات کامل درخواست و پاسخ سیستم
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 mt-4 overflow-y-auto">
            <div className="space-y-6 p-1">
              {/* User & ID Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 bg-gray-50 dark:bg-gray-800 p-3 rounded-md border">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-500">درخواست کننده</span>
                    <span className="font-bold">{selectedRequest?.username || "Unknown"}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-500">شناسه کاربر</span>
                    <span className="font-mono text-xs text-gray-400">{selectedRequest?.user_id}</span>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium mb-1 text-gray-500">نوع کوئری</h4>
                  <p className="text-sm font-mono bg-gray-100 dark:bg-gray-800 p-2 rounded">
                    {selectedRequest?.query_type || selectedRequest?.request_type || "N/A"}
                  </p>
                </div>
                <div>
                  <h4 className="text-sm font-medium mb-1 text-gray-500">کد رهگیری اصلی</h4>
                  <p className="text-sm font-mono bg-gray-100 dark:bg-gray-800 p-2 rounded">
                    {selectedRequest?.original_request_id || "N/A"}
                  </p>
                </div>
                <div className="col-span-2">
                  <h4 className="text-sm font-medium mb-1 text-gray-500">شناسه سیستم (ID)</h4>
                  <p className="text-sm font-mono bg-gray-100 dark:bg-gray-800 p-2 rounded">
                    {selectedRequest?.id}
                  </p>
                </div>
              </div>

              {/* Request Content */}
              <div>
                <h4 className="text-sm font-medium mb-2">محتوای درخواست (Query Params)</h4>
                <div className="rounded-md bg-gray-950 p-4 overflow-auto">
                  <pre className="text-xs text-gray-50 font-mono">
                    {JSON.stringify(selectedRequest?.content || selectedRequest?.query_params || {}, null, 2)}
                  </pre>
                </div>
              </div>

              {/* Response/Result */}
              <div>
                <h4 className="text-sm font-medium mb-2">نتیجه / پاسخ</h4>
                {selectedRequest?.error ? (
                  <Alert variant="destructive">
                    <AlertTitle>خطا در پردازش</AlertTitle>
                    <AlertDescription>{selectedRequest.error}</AlertDescription>
                  </Alert>
                ) : (
                  <div className="rounded-md bg-gray-950 p-4 overflow-auto max-h-[300px]">
                    <pre className="text-xs text-green-400 font-mono">
                      {JSON.stringify(selectedRequest?.result || {}, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
