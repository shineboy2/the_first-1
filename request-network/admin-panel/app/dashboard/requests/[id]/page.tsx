"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth-store";
import {
    ArrowRight,
    Loader2,
    Activity,
    Server,
    Database,
    AlertCircle,
    CheckCircle2,
    XCircle,
    Clock,
    Box,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Label } from "@/components/ui/label";

import { requestService } from "@/lib/services/admin-api";
import type { Request } from "@/lib/services/admin-api";

export default function RequestDetailsPage({ params }: { params: { id: string } }) {
    const router = useRouter();
    const { user: currentUser } = useAuthStore();
    const [request, setRequest] = useState<Request | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchRequestData = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await requestService.getRequestById(params.id);
            setRequest(data);
        } catch (err: any) {
            console.error("Error fetching request data:", err);
            setError(err?.response?.data?.detail || "خطا در دریافت اطلاعات درخواست");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (currentUser) {
            fetchRequestData();
        }
    }, [params.id, currentUser]);

    const getStatusIcon = (status: string) => {
        const normalized = (request as any)?.effective_status?.toLowerCase?.() || status?.toLowerCase();
        switch (normalized) {
            case "completed_success":
            case "success":
                return <CheckCircle2 className="h-6 w-6 text-green-500" />;
            case "completed_error":
            case "completed":
                return <AlertCircle className="h-6 w-6 text-orange-500" />;
            case "failed":
                return <XCircle className="h-6 w-6 text-red-500" />;
            case "pending":
            case "processing":
            default:
                return <Clock className="h-6 w-6 text-amber-500" />;
        }
    };

    const getStatusBadge = (status: string) => {
        const normalized = (request as any)?.effective_status?.toLowerCase?.() || status?.toLowerCase();
        switch (normalized) {
            case "completed_success":
            case "success":
                return <Badge className="bg-green-100 text-green-800 hover:bg-green-200">وضعیت: موفق ✓</Badge>;
            case "completed_error":
            case "completed":
                return <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-200">تکمیل شده (خطا)</Badge>;
            case "failed":
                return <Badge variant="destructive">وضعیت: خطا</Badge>;
            default:
                return <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-200">در حال انجام</Badge>;
        }
    };

    // Helper to extract and render base64 images from JSON response
    const renderMediaFromResponse = (data: any) => {
        if (!data) return null;

        const mediaItems: { key: string, src: string }[] = [];

        // Recursive function to find base64 images in the object
        const extractImages = (obj: any, path: string = "") => {
            if (!obj || typeof obj !== "object") return;

            Object.entries(obj).forEach(([key, value]) => {
                const currentPath = path ? `${path}.${key}` : key;

                if (typeof value === "string") {
                    // Check if string is base64 image data uri
                    if (value.startsWith("data:image/") && value.includes(";base64,")) {
                        mediaItems.push({ key: currentPath, src: value });
                    }
                } else if (typeof value === "object") {
                    extractImages(value, currentPath);
                }
            });
        };

        extractImages(data);

        if (mediaItems.length === 0) return null;

        return (
            <div className="mt-6 mb-4">
                <Label className="text-sm font-semibold mb-3 flex items-center gap-2">
                    <Box className="h-4 w-4" />
                    تصاویر خروجی ({mediaItems.length})
                </Label>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                    {mediaItems.map((item, index) => (
                        <div key={index} className="border rounded-lg p-2 bg-white dark:bg-slate-800 shadow-sm flex flex-col">
                            <div className="relative w-full aspect-square bg-slate-100 dark:bg-slate-900 rounded-md overflow-hidden flex items-center justify-center">
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img
                                    src={item.src}
                                    alt={item.key}
                                    className="max-w-full max-h-full object-contain"
                                    onClick={() => window.open(item.src, "_blank")}
                                    style={{ cursor: "pointer" }}
                                />
                            </div>
                            <div className="mt-2 text-xs truncate text-center text-slate-500 font-mono px-1">
                                {item.key}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    if (loading && !request) {
        return (
            <div className="flex min-h-screen justify-center items-center">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    if (!request || error) {
        return (
            <div className="p-8">
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>خطا</AlertTitle>
                    <AlertDescription>{error || "درخواست یافت نشد."}</AlertDescription>
                </Alert>
                <Button variant="outline" className="mt-4" onClick={() => router.push("/dashboard/requests")}>
                    بازگشت به لیست
                </Button>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-12">
            {/* Header */}
            <div className="border-b bg-white dark:bg-gray-800 hidden md:block">
                <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                    <div className="flex items-start gap-4">
                        <Button variant="ghost" size="icon" onClick={() => router.push("/dashboard/requests")} className="mt-1">
                            <ArrowRight className="h-5 w-5" />
                        </Button>
                        <div className="flex-1">
                            <div className="flex items-center gap-3">
                                {getStatusIcon(request.status)}
                                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                                    درخواست: {request.name || request.request_type || request.query_type || 'نامشخص'}
                                </h1>
                                {getStatusBadge(request.status)}
                            </div>
                            <p className="mt-2 text-sm text-gray-500 font-mono">ID: {request.id}</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* General Metadata */}
                    <Card className="col-span-1 border-t-4 border-t-primary shadow-sm">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-primary">
                                <Activity className="h-5 w-5" />
                                اطلاعات پردازش
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4 text-sm">
                            <div>
                                <Label className="text-gray-500">نوع کوئری (سرویس)</Label>
                                <div className="mt-1 font-mono font-bold">{request.query_type}</div>
                            </div>
                            <div>
                                <Label className="text-gray-500">شناسه کاربر ثبت کننده</Label>
                                <div className="mt-1 font-mono hover:text-blue-500 cursor-pointer transition-colors"
                                    onClick={() => router.push(`/dashboard/users/${request.user_id}`)}>
                                    {request.user_id}
                                </div>
                            </div>
                            {request.sub_user_id && (
                                <div>
                                    <Label className="text-gray-500">شناسه ساب‌یوزر (Sub-user)</Label>
                                    <div className="mt-1 font-mono">{request.sub_user_id}</div>
                                </div>
                            )}
                            <div>
                                <Label className="text-gray-500">تاریخ ثبت درخواست</Label>
                                <div className="mt-1" dir="ltr">{new Date(request.created_at).toLocaleString("fa-IR")}</div>
                            </div>
                            <div>
                                <Label className="text-gray-500">اولویت پردازش شبکه</Label>
                                <div className="mt-1">
                                    <Badge variant="outline">Priority {request.priority || 0}</Badge>
                                </div>
                            </div>
                            {request.meta && Object.keys(request.meta).length > 0 && (
                                <div className="pt-2 border-t">
                                    <Label className="text-gray-500 mb-2 block">متا دیتا و هدرها</Label>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded text-xs font-mono break-all" dir="ltr">
                                        <ul className="space-y-1">
                                            {Object.entries(request.meta).map(([key, value]) => (
                                                <li key={key}><span className="text-gray-500">{key}:</span> {String(value)}</li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Payload Viewer */}
                    <Card className="col-span-1 lg:col-span-2 shadow-sm relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 dark:bg-indigo-900/20 rounded-bl-full -z-10" />
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Database className="h-5 w-5 text-indigo-500" />
                                پارامترهای ورودی (Payload / Query Params)
                            </CardTitle>
                            <CardDescription>مقادیری که کلاینت هنگام ثبت این درخواست به سرور ارسال کرده است.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <pre className="p-4 bg-gray-950 text-green-400 rounded-lg overflow-x-auto text-xs font-mono leading-relaxed border border-gray-800 shadow-inner" dir="ltr">
                                {JSON.stringify(request.query_params || {}, null, 2)}
                            </pre>
                        </CardContent>
                    </Card>

                    {/* Response Viewer */}
                    <Card className="col-span-1 lg:col-span-3 border-t-4 border-t-green-500 shadow-sm mt-4">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Server className="h-5 w-5 text-green-500" />
                                نتیجه اجرای شبکه دیود (Response Result)
                            </CardTitle>
                            <CardDescription>
                                در صورتی که درخواست در شبکه Response پردازش شده و نتیجه آن برگشت داده شده باشد، اطلاعات خروجی در این بخش نمایش داده می‌شود.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {!request.response && (request as any)?.effective_status !== 'completed_error' && request.status !== 'failed' ? (
                                <div className="text-center py-12 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-dashed border-gray-300 dark:border-gray-700">
                                    <Box className="h-10 w-10 text-gray-400 mx-auto mb-3 opacity-50" />
                                    <p className="text-gray-500 font-medium">پاسخی برای این درخواست ثبت نشده است.</p>
                                    <p className="text-xs text-gray-400 mt-1">ممکن است درخواست هنوز در صف پردازش باشد.</p>
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    {((request as any)?.error_message || (request.response && request.response.error_message)) && (
                                        <Alert variant="destructive" className="mb-4">
                                            <AlertCircle className="h-4 w-4" />
                                            <AlertTitle>خطا در پردازش</AlertTitle>
                                            <AlertDescription>
                                                {(request as any).error_message || request.response?.error_message}
                                            </AlertDescription>
                                        </Alert>
                                    )}
                                    <div className="flex flex-wrap gap-4 mb-4">
                                        {request.response.execution_time_ms && (
                                            <Badge variant="outline" className="bg-blue-50 text-blue-800 border-blue-200">
                                                زمان اجرا: {request.response.execution_time_ms} ms
                                            </Badge>
                                        )}
                                        <span className="text-xs text-gray-500 flex items-center">
                                            دریافت در: {new Date(request.response.received_at || request.response.created_at).toLocaleString('fa-IR')}
                                        </span>
                                    </div>

                                    {/* Handle Media Rendering */}
                                    {renderMediaFromResponse(
                                        typeof request.response.result_data === 'string' 
                                            ? (() => { try { return JSON.parse(request.response.result_data); } catch(e) { return null; } })()
                                            : request.response.result_data
                                    )}

                                    {/* Grouped Results by Index (new format) */}
                                    {(() => {
                                        const resultData = typeof request.response.result_data === 'string'
                                            ? (() => { try { return JSON.parse(request.response.result_data); } catch(e) { return null; } })()
                                            : request.response.result_data;

                                        if (resultData && resultData.results_by_index && typeof resultData.results_by_index === 'object') {
                                            const indexEntries = Object.entries(resultData.results_by_index as Record<string, any[]>);
                                            return (
                                                <div className="space-y-4">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <Database className="h-4 w-4 text-indigo-500" />
                                                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                                            تعداد کل نتایج: {resultData.count || 0} — از {indexEntries.length} منبع
                                                        </span>
                                                    </div>
                                                    {indexEntries.map(([indexName, records]) => (
                                                        <Card key={indexName} className="border-r-4 border-r-indigo-400">
                                                            <CardHeader className="pb-2">
                                                                <CardTitle className="text-base flex items-center gap-2">
                                                                    <Server className="h-4 w-4 text-indigo-500" />
                                                                    {indexName}
                                                                    <Badge variant="secondary" className="text-xs">
                                                                        {(records as any[]).length} رکورد
                                                                    </Badge>
                                                                </CardTitle>
                                                            </CardHeader>
                                                            <CardContent>
                                                                <div className="overflow-x-auto">
                                                                    {(records as any[]).length > 0 && (
                                                                        <table className="w-full text-sm border-collapse">
                                                                            <thead>
                                                                                <tr className="bg-gray-100 dark:bg-gray-800">
                                                                                    {Object.keys((records as any[])[0]).map((key) => (
                                                                                        <th key={key} className="px-3 py-2 text-right font-medium text-gray-600 dark:text-gray-400 border-b">
                                                                                            {key}
                                                                                        </th>
                                                                                    ))}
                                                                                </tr>
                                                                            </thead>
                                                                            <tbody>
                                                                                {(records as any[]).map((row: any, rowIdx: number) => (
                                                                                    <tr key={rowIdx} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800/50">
                                                                                        {Object.values(row).map((val: any, colIdx: number) => (
                                                                                            <td key={colIdx} className="px-3 py-2 text-gray-800 dark:text-gray-200">
                                                                                                {typeof val === 'object' ? JSON.stringify(val) : String(val ?? '')}
                                                                                            </td>
                                                                                        ))}
                                                                                    </tr>
                                                                                ))}
                                                                            </tbody>
                                                                        </table>
                                                                    )}
                                                                </div>
                                                            </CardContent>
                                                        </Card>
                                                    ))}
                                                </div>
                                            );
                                        }
                                        return null;
                                    })()}

                                    <div className="mt-4">
                                        <Label className="text-xs text-gray-500 mb-2 block">داده‌های خام (JSON)</Label>
                                        <pre className="p-4 bg-[#0d1117] text-[#e6edf3] rounded-lg overflow-x-auto text-xs font-mono leading-relaxed shadow-inner border border-gray-800" dir="ltr">
                                            {typeof request.response.result_data === 'string' 
                                                ? (() => {
                                                    try {
                                                        return JSON.stringify(JSON.parse(request.response.result_data), null, 2);
                                                    } catch (e) {
                                                        return request.response.result_data;
                                                    }
                                                })() 
                                                : JSON.stringify(request.response.result_data, null, 2)}
                                        </pre>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
