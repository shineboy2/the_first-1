"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth-store";
import {
    Search,
    Eye,
    RefreshCw,
    AlertCircle,
    Clock,
    CheckCircle2,
    XCircle,
    FileText,
    Plus
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2 } from "lucide-react";

import { requestService } from "@/lib/services/admin-api";
import type { Request } from "@/lib/services/admin-api";

interface RequestsState {
    requests: Request[];
    loading: boolean;
    error: string | null;
    searchTerm: string;
}

export default function RequestsPage() {
    const router = useRouter();
    const { user: currentUser, isLoading: authLoading } = useAuthStore();
    const [state, setState] = useState<RequestsState>({
        requests: [],
        loading: true,
        error: null,
        searchTerm: "",
    });

    const fetchRequests = async () => {
        try {
            setState((prev) => ({ ...prev, loading: true, error: null }));
            const data = currentUser?.profile_type === 'admin'
                ? await requestService.getAllRequests(0, 1000)
                : await requestService.getUserRequests(0, 1000);
            setState((prev) => ({
                ...prev,
                requests: Array.isArray(data) ? data : [],
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

    useEffect(() => {
        if (!authLoading && currentUser) {
            fetchRequests();
        }
    }, [authLoading, currentUser]);

    const handleRefresh = () => fetchRequests();

    const handleDetailsClick = (req: Request) => {
        // We will build this page next
        router.push(`/dashboard/requests/${req.id}`);
    };

    const getStatusIcon = (status: string) => {
        const normalized = status.toLowerCase();
        if (normalized === "completed_success" || normalized === "success") {
            return <CheckCircle2 className="h-4 w-4 text-green-500 mr-1" />;
        }
        if (normalized === "completed_error" || normalized === "completed") {
            return <AlertCircle className="h-4 w-4 text-orange-500 mr-1" />;
        }
        if (normalized === "failed") {
            return <XCircle className="h-4 w-4 text-red-500 mr-1" />;
        }
        return <Clock className="h-4 w-4 text-amber-500 mr-1" />;
    };

    const getStatusBadge = (status: string) => {
        const normalized = status.toLowerCase();
        if (normalized === "completed_success") {
            return <Badge className="bg-green-100 text-green-800 hover:bg-green-100 border-green-200">موفق ✓</Badge>;
        }
        if (normalized === "completed_error" || normalized === "completed") {
            return <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-100 border-orange-200">تکمیل شده (خطا)</Badge>;
        }
        if (normalized === "failed") {
            return <Badge variant="destructive" className="bg-red-100 text-red-800 hover:bg-red-100 border-red-200">خطا</Badge>;
        }
        if (normalized === "processing") {
            return <Badge variant="secondary" className="bg-blue-100 text-blue-800 hover:bg-blue-100 border-blue-200">درحال پردازش</Badge>;
        }
        return <Badge variant="secondary" className="bg-amber-100 text-amber-800 hover:bg-amber-100 border-amber-200">درانتظار</Badge>;
    };

    const filteredRequests = state.requests.filter(
        (req) =>
            req.name.toLowerCase().includes(state.searchTerm.toLowerCase()) ||
            req.query_type.toLowerCase().includes(state.searchTerm.toLowerCase()) ||
            req.id.includes(state.searchTerm)
    );

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
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                                <FileText className="h-8 w-8" />
                                مدیریت درخواست‌ها (Requests)
                            </h1>
                            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                مشاهده تمامی درخواست‌های ثبت شده در سیستم
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button
                                onClick={() => router.push("/dashboard/requests/new")}
                                className="gap-2"
                            >
                                <Plus className="h-4 w-4" />
                                ثبت درخواست جدید
                            </Button>
                            <Button
                                variant="outline"
                                size="icon"
                                onClick={handleRefresh}
                                disabled={state.loading}
                            >
                                <RefreshCw className={`h-4 w-4 ${state.loading ? "animate-spin" : ""}`} />
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {state.error && (
                    <Alert variant="destructive" className="mb-6">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>خطا</AlertTitle>
                        <AlertDescription>{state.error}</AlertDescription>
                    </Alert>
                )}

                {/* Stats */}
                <div className="grid gap-4 md:grid-cols-4 mb-6">
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
                            <CardTitle className="text-sm font-medium">موفق</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-green-600">
                                {state.requests.filter((r) => (r as any).effective_status?.toLowerCase?.() === "completed_success").length}
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">در حال انجام / معلق</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-amber-600">
                                {state.requests.filter((r) => {
                                    const s = r.status.toLowerCase();
                                    return !s.startsWith("completed") && s !== "failed";
                                }).length}
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">خطا خورده</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-red-600">
                                {state.requests.filter((r) => r.status.toLowerCase() === "failed").length}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                <Card className="mb-6">
                    <CardHeader>
                        <CardTitle>فیلتر و جستجو</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="relative max-w-md">
                            <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                            <Input
                                placeholder="جستجو با عنوان، سرویس یا شناسه..."
                                value={state.searchTerm}
                                onChange={(e) =>
                                    setState((prev) => ({ ...prev, searchTerm: e.target.value }))
                                }
                                className="pr-10"
                            />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>لیست درخواست‌های ثبت شده</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {state.loading ? (
                            <div className="flex justify-center py-8">
                                <Loader2 className="h-6 w-6 animate-spin" />
                            </div>
                        ) : (
                            <div className="rounded-md border">
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>عنوان (نام عملیات)</TableHead>
                                            <TableHead>سرویس (Query Type)</TableHead>
                                            <TableHead className="text-center">وضعیت</TableHead>
                                            <TableHead className="text-center">تاریخ ایجاد</TableHead>
                                            <TableHead className="text-center">جزئیات</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {filteredRequests.length > 0 ? (
                                            filteredRequests.map((req) => (
                                                <TableRow key={req.id}>
                                                    <TableCell className="font-medium">
                                                        <div className="flex items-center">
                                                            {req.name || req.request_type || req.query_type || 'نامشخص'}
                                                            {req.query_type === "web_search" && <Badge variant="outline" className="ml-2 text-[10px]">جستجو</Badge>}
                                                        </div>
                                                        <div className="text-xs text-muted-foreground mt-1 font-mono">{req.id.split("-")[0]}</div>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Badge variant="outline" className="font-mono">
                                                            {req.query_type}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="text-center flex items-center justify-center">
                                                        {getStatusBadge((req as any).effective_status || req.status)}
                                                    </TableCell>
                                                    <TableCell className="text-center" dir="ltr">
                                                        <span className="text-sm text-muted-foreground whitespace-nowrap">
                                                            {new Date(req.created_at).toLocaleString("fa-IR")}
                                                        </span>
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <Button variant="ghost" size="sm" onClick={() => handleDetailsClick(req)}>
                                                            <Eye className="h-4 w-4 text-blue-500" />
                                                        </Button>
                                                    </TableCell>
                                                </TableRow>
                                            ))
                                        ) : (
                                            <TableRow>
                                                <TableCell colSpan={5} className="text-center py-12">
                                                    <p className="text-muted-foreground mb-4">درخواستی یافت نشد</p>
                                                    <Button variant="outline" onClick={() => router.push("/dashboard/requests/new")}>
                                                        <Plus className="h-4 w-4 mr-2" />
                                                        ثبت اولین درخواست
                                                    </Button>
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
        </div>
    );
}
