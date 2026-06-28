"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth-store";
import {
    ArrowRight,
    Loader2,
    Key,
    Shield,
    Activity,
    Trash2,
    Plus,
    RefreshCw,
    AlertCircle,
    CheckCircle2,
    List,
    Lock,
    Globe,
    FileText,
    BarChart3
} from "lucide-react";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from "recharts";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
    CardFooter,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Label } from "@/components/ui/label";

import { userService, apiKeyService, rateLimitService, requestService, auditLogService } from "@/lib/services/admin-api";
import type { User, APIKey, RateLimitStats, Request as ApiRequest } from "@/lib/services/admin-api";

export default function UserDetailsPage({ params }: { params: { id: string } }) {
    const router = useRouter();
    const { user: currentUser } = useAuthStore();

    const [user, setUser] = useState<User | null>(null);
    const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
    const [rateLimit, setRateLimit] = useState<RateLimitStats | null>(null);
    const [requests, setRequests] = useState<ApiRequest[]>([]);
    const [auditLogs, setAuditLogs] = useState<any[]>([]);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // API Key Form State
    const [newKeyName, setNewKeyName] = useState("");
    const [generatedKey, setGeneratedKey] = useState<string | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);

    // Edit IPs State
    const [isEditingIps, setIsEditingIps] = useState(false);
    const [editIpsInput, setEditIpsInput] = useState("");
    const [isSavingIps, setIsSavingIps] = useState(false);

    // Rate Limit Form State (kept for reset only)

    const fetchUserData = async () => {
        try {
            setLoading(true);
            setError(null);
            setGeneratedKey(null);

            const [userData, keysData, userRequests, logsData] = await Promise.all([
                userService.getUserById(params.id),
                apiKeyService.getUserApiKeys(params.id),
                requestService.getAllRequests(0, 100, params.id).catch(() => []),
                auditLogService.getLogs({ user_id: params.id, limit: 50 }).catch(() => ({ items: [] }))
            ]);

            setUser(userData);
            setApiKeys(Array.isArray(keysData) ? keysData : []);
            setRequests(Array.isArray(userRequests) ? userRequests : []);
            setAuditLogs(logsData?.items || []);
            setRateLimit(userData.rate_limit_stats ?? null);

            // Rate limit data loaded

        } catch (err: any) {
            console.error("Error fetching user data:", err);
            setError(err?.response?.data?.detail || "خطا در دریافت اطلاعات کاربر");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (currentUser) {
            fetchUserData();
        } else if (currentUser === null) {
            router.push("/login");
        }
    }, [params.id, currentUser]);

    const handleCreateApiKey = async () => {
        if (!newKeyName.trim()) return;
        try {
            setIsGenerating(true);
            setError(null);
            const result = await apiKeyService.createUserApiKey(params.id, newKeyName);
            setGeneratedKey(result.api_key || null);
            setNewKeyName("");
            // Refresh list
            const keysData = await apiKeyService.getUserApiKeys(params.id);
            setApiKeys(Array.isArray(keysData) ? keysData : []);
        } catch (err: any) {
            setError(err?.response?.data?.detail || "خطا در ساخت کلید API");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleRevokeApiKey = async (keyId: string) => {
        if (!confirm("آیا از ابطال این کلید اطمینان دارید؟")) return;
        try {
            setLoading(true);
            await apiKeyService.revokeUserApiKey(params.id, keyId);
            const keysData = await apiKeyService.getUserApiKeys(params.id);
            setApiKeys(Array.isArray(keysData) ? keysData : []);
        } catch (err: any) {
            setError(err?.response?.data?.detail || "خطا در ابطال کلید");
        } finally {
            setLoading(false);
        }
    };

    // Custom limits removed - limits come from Response Network

    const handleResetLimits = async () => {
        if (!confirm("آیا از بازنشانی ظرفیت‌های مصرف شده این کاربر اطمینان دارید؟")) return;
        try {
            setLoading(true);
            await rateLimitService.resetUserRateLimit(params.id, "all");
            const limitsData = await rateLimitService.getUserRateLimitStats(params.id);
            setRateLimit(limitsData);
            alert("بازنشانی با موفقیت انجام شد.");
        } catch (err: any) {
            setError(err?.response?.data?.detail || "خطا در بازنشانی");
        } finally {
            setLoading(false);
        }
    };

    if (loading && !user) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    if (!user) {
        return (
            <div className="p-8">
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>خطا</AlertTitle>
                    <AlertDescription>کاربر یافت نشد.</AlertDescription>
                </Alert>
                <Button variant="outline" className="mt-4" onClick={() => router.push("/dashboard/users")}>
                    بازگشت به لیست
                </Button>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-12">
            {/* Header */}
            <div className="border-b bg-white dark:bg-gray-800">
                <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="icon" onClick={() => router.push("/dashboard/users")}>
                            <ArrowRight className="h-5 w-5" />
                        </Button>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                                جزئیات کاربر: {user.username}
                                <Badge variant={user.is_active ? "default" : "destructive"}>
                                    {user.is_active ? "فعال" : "غیرفعال"}
                                </Badge>
                            </h1>
                            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                مدیریت دسترسی‌ها، کلیدهای API و محدودیت نرخ (Rate Limit)
                            </p>
                        </div>
                        <div className="mr-auto">
                            <Button variant="outline" size="sm" onClick={fetchUserData} disabled={loading}>
                                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                                به‌روزرسانی
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
                {error && (
                    <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>خطا</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* User Info Card */}
                    <Card className="col-span-1 border-t-4 border-t-primary">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Shield className="h-5 w-5" />
                                اطلاعات کاربری
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <Label className="text-gray-500">شناسه (ID)</Label>
                                <div className="font-mono text-sm mt-1 select-all break-all">{user.id}</div>
                            </div>
                            <div>
                                <Label className="text-gray-500">ایمیل</Label>
                                <div className="mt-1">{user.email}</div>
                            </div>
                            <div>
                                <Label className="text-gray-500">نوع پروفایل</Label>
                                <div className="mt-1 font-medium capitalize">{user.profile_type}</div>
                            </div>
                            <div>
                                <Label className="text-gray-500">تاریخ تایید عضویت</Label>
                                <div className="mt-1" dir="ltr">{new Date(user.created_at).toLocaleString("fa-IR")}</div>
                            </div>
                            <div className="pt-4 border-t">
                                <div className="flex justify-between items-start">
                                    <Label className="text-gray-500 flex items-center gap-2">
                                        <Shield className="h-4 w-4" />
                                        آی‌پی‌های مجاز (Allowed IPs)
                                    </Label>
                                    {!isEditingIps ? (
                                        <Button variant="ghost" size="sm" onClick={() => {
                                            setEditIpsInput(user.allowed_ips ? user.allowed_ips.join(", ") : "");
                                            setIsEditingIps(true);
                                        }}>
                                            ویرایش
                                        </Button>
                                    ) : (
                                        <div className="flex gap-2">
                                            <Button variant="ghost" size="sm" onClick={() => setIsEditingIps(false)} disabled={isSavingIps}>
                                                انصراف
                                            </Button>
                                            <Button size="sm" onClick={async () => {
                                                try {
                                                    setIsSavingIps(true);
                                                    const ips = editIpsInput.split(",").map(i => i.trim()).filter(Boolean);
                                                    const updatedUser = await userService.updateUserAllowedIps(params.id, ips);
                                                    setUser(updatedUser);
                                                    setIsEditingIps(false);
                                                } catch (err: any) {
                                                    setError(err?.response?.data?.detail || "خطا در بروزرسانی آی‌پی‌ها");
                                                } finally {
                                                    setIsSavingIps(false);
                                                }
                                            }} disabled={isSavingIps}>
                                                {isSavingIps ? <Loader2 className="h-3 w-3 animate-spin" /> : "ذخیره"}
                                            </Button>
                                        </div>
                                    )}
                                </div>
                                
                                {isEditingIps ? (
                                    <div className="mt-2 space-y-2">
                                        <Input
                                            value={editIpsInput}
                                            onChange={(e) => setEditIpsInput(e.target.value)}
                                            placeholder="192.168.1.1, 10.0.0.1"
                                            className="font-mono text-left"
                                            dir="ltr"
                                        />
                                        <p className="text-xs text-amber-600 dark:text-amber-400">توجه: این تغییرات ممکن است با همگام‌سازی از شبکه پاسخ بازنویسی شوند.</p>
                                    </div>
                                ) : (
                                    <div className="mt-2 flex flex-wrap gap-2">
                                        {user.allowed_ips && user.allowed_ips.length > 0 ? (
                                            user.allowed_ips.map((ip: string, index: number) => (
                                                <Badge key={index} variant="outline" className="font-mono bg-gray-100 dark:bg-gray-800">
                                                    {ip}
                                                </Badge>
                                            ))
                                        ) : (
                                            <span className="text-sm text-gray-400">همه آی‌پی‌ها مجاز هستند</span>
                                        )}
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Rate Limit Stats & Controls */}
                    <Card className="col-span-1 md:col-span-2 border-t-4 border-t-amber-500">
                        <CardHeader>
                            <CardTitle className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <Activity className="h-5 w-5" />
                                    محدودیت نرخ درخواست (Rate Limits)
                                </div>
                                <Button variant="secondary" size="sm" onClick={handleResetLimits} disabled={loading}>
                                    بازنشانی مصارف
                                </Button>
                            </CardTitle>
                            <CardDescription>
                                محدودیت‌های نرخ درخواست از شبکه پاسخ سینک شده و قابل ویرایش در آنجا هستند. در اینجا فقط امکان بازنشانی شمارنده‌ها وجود دارد.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-6">
                                {/* Synced limits from User model */}
                                <div className="grid grid-cols-3 gap-4 text-center">
                                    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                        <div className="text-lg font-bold">{user.rate_limit_per_minute ?? '—'}</div>
                                        <div className="text-xs text-gray-500">حداکثر در دقیقه</div>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                        <div className="text-lg font-bold">{user.rate_limit_per_hour ?? '—'}</div>
                                        <div className="text-xs text-gray-500">حداکثر در ساعت</div>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                        <div className="text-lg font-bold">{user.rate_limit_per_day ?? '—'}</div>
                                        <div className="text-xs text-gray-500">حداکثر در روز</div>
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4 text-center">
                                    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                        <div className="text-lg font-bold">{user.daily_request_limit ?? '—'}</div>
                                        <div className="text-xs text-gray-500">سقف درخواست روزانه</div>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                        <div className="text-lg font-bold">{user.monthly_request_limit ?? '—'}</div>
                                        <div className="text-xs text-gray-500">سقف درخواست ماهانه</div>
                                    </div>
                                </div>

                                {/* Current usage from Redis */}
                                {rateLimit && (
                                    <div className="border-t pt-4">
                                        <h4 className="text-sm font-semibold mb-3">مصرف فعلی (Redis)</h4>
                                        <div className="grid grid-cols-3 gap-4 text-center">
                                            <div className="p-3 rounded-lg border">
                                                <div className="text-base font-mono">{rateLimit.usage?.minute ?? 0}</div>
                                                <div className="text-xs text-gray-500">در دقیقه ({rateLimit.percentages?.minute ?? 0}%)</div>
                                            </div>
                                            <div className="p-3 rounded-lg border">
                                                <div className="text-base font-mono">{rateLimit.usage?.hour ?? 0}</div>
                                                <div className="text-xs text-gray-500">در ساعت ({rateLimit.percentages?.hour ?? 0}%)</div>
                                            </div>
                                            <div className="p-3 rounded-lg border">
                                                <div className="text-base font-mono">{rateLimit.usage?.day ?? 0}</div>
                                                <div className="text-xs text-gray-500">در روز ({rateLimit.percentages?.day ?? 0}%)</div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Access Control Card */}
                <Card className="border-t-4 border-t-green-500">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <List className="h-5 w-5" />
                            دسترسی به انواع درخواست
                        </CardTitle>
                        <CardDescription>
                            انواع درخواست‌هایی که این کاربر مجاز به ارسال آن‌هاست. این اطلاعات از شبکه پاسخ سینک می‌شوند.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {/* Allowed Request Types */}
                        <div>
                            <Label className="text-gray-500 flex items-center gap-1 mb-2">
                                <CheckCircle2 className="h-4 w-4 text-green-500" />
                                انواع درخواست مجاز
                            </Label>
                            <div className="flex flex-wrap gap-2">
                                {user.allowed_request_types && user.allowed_request_types.length > 0 ? (
                                    user.allowed_request_types.map((type: string) => (
                                        <Badge key={type} variant="default" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                                            {type}
                                        </Badge>
                                    ))
                                ) : (
                                    <span className="text-sm text-gray-400">هیچ نوع درخواستی تعریف نشده (دسترسی بسته)</span>
                                )}
                            </div>
                        </div>

                        {/* Blocked Request Types */}
                        <div>
                            <Label className="text-gray-500 flex items-center gap-1 mb-2">
                                <Lock className="h-4 w-4 text-red-500" />
                                انواع درخواست مسدود شده
                            </Label>
                            <div className="flex flex-wrap gap-2">
                                {user.blocked_request_types && user.blocked_request_types.length > 0 ? (
                                    user.blocked_request_types.map((type: string) => (
                                        <Badge key={type} variant="destructive">
                                            {type}
                                        </Badge>
                                    ))
                                ) : (
                                    <span className="text-sm text-gray-400">هیچ نوع درخواستی مسدود نشده</span>
                                )}
                            </div>
                        </div>

                        {/* Allowed External APIs */}
                        <div>
                            <Label className="text-gray-500 flex items-center gap-1 mb-2">
                                <Globe className="h-4 w-4 text-blue-500" />
                                APIهای خارجی مجاز
                            </Label>
                            <div className="flex flex-wrap gap-2">
                                {user.allowed_external_apis && user.allowed_external_apis.length > 0 ? (
                                    user.allowed_external_apis.map((api: string) => (
                                        <Badge key={api} className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                                            {api}
                                        </Badge>
                                    ))
                                ) : (
                                    <span className="text-sm text-gray-400">هیچ API خارجی تعریف نشده</span>
                                )}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* User Requests & Success Rate */}
                <Card className="border-t-4 border-t-blue-500">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <BarChart3 className="h-5 w-5" />
                            درخواست‌های کاربر و نرخ موفقیت
                        </CardTitle>
                        <CardDescription>
                            نمایش 100 درخواست اخیر کاربر و نمودار وضعیت آن‌ها بر اساس نوع درخواست
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {(() => {
                            if (requests.length === 0) {
                                return <p className="text-sm text-gray-500 text-center py-4">درخواستی برای این کاربر یافت نشد.</p>;
                            }

                            // Calculate stats for chart
                            const statsMap: Record<string, { name: string, success: number, failed: number, pending: number }> = {};
                            requests.forEach(req => {
                                const type = req.request_type || req.query_type || "نامشخص";
                                if (!statsMap[type]) {
                                    statsMap[type] = { name: type, success: 0, failed: 0, pending: 0 };
                                }
                                const status = req.status.toLowerCase();
                                if (status.includes("success") || (status === "completed" && !req.error)) {
                                    statsMap[type].success++;
                                } else if (status.includes("fail") || status.includes("error")) {
                                    statsMap[type].failed++;
                                } else {
                                    statsMap[type].pending++;
                                }
                            });
                            const chartData = Object.values(statsMap);

                            return (
                                <div className="space-y-8">
                                    <div className="h-[300px] w-full" dir="ltr">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis dataKey="name" />
                                                <YAxis />
                                                <Tooltip />
                                                <Legend />
                                                <Bar dataKey="success" name="موفق" stackId="a" fill="#22c55e" />
                                                <Bar dataKey="failed" name="خطا" stackId="a" fill="#ef4444" />
                                                <Bar dataKey="pending" name="در انتظار" stackId="a" fill="#eab308" />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>

                                    <div className="rounded-md border max-h-[400px] overflow-auto">
                                        <Table>
                                            <TableHeader>
                                                <TableRow>
                                                    <TableHead>نوع درخواست</TableHead>
                                                    <TableHead>وضعیت</TableHead>
                                                    <TableHead>تاریخ</TableHead>
                                                    <TableHead>آی‌دی درخواست</TableHead>
                                                </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {requests.slice(0, 10).map((req) => {
                                                    const statusLower = req.status.toLowerCase();
                                                    let badgeVariant: "default" | "destructive" | "secondary" = "secondary";
                                                    let statusText = req.status;

                                                    if (statusLower.includes("success") || (statusLower === "completed" && !req.error)) {
                                                        badgeVariant = "default";
                                                        statusText = "موفق ✓";
                                                    } else if (statusLower.includes("fail") || statusLower.includes("error")) {
                                                        badgeVariant = "destructive";
                                                        statusText = "خطا";
                                                    }

                                                    return (
                                                        <TableRow key={req.id}>
                                                            <TableCell className="font-medium">{req.request_type || req.query_type}</TableCell>
                                                            <TableCell>
                                                                <Badge variant={badgeVariant} className={badgeVariant === "default" ? "bg-green-100 text-green-800 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-300" : ""}>
                                                                    {statusText}
                                                                </Badge>
                                                            </TableCell>
                                                            <TableCell dir="ltr" className="text-sm">
                                                                {new Date(req.created_at).toLocaleString("fa-IR")}
                                                            </TableCell>
                                                            <TableCell className="font-mono text-xs text-gray-500">
                                                                {req.id.substring(0, 8)}...
                                                            </TableCell>
                                                        </TableRow>
                                                    );
                                                })}
                                            </TableBody>
                                        </Table>
                                    </div>
                                </div>
                            );
                        })()}
                    </CardContent>
                </Card>

                {/* API Keys Table */}
                <Card className="border-t-4 border-t-purple-500">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Key className="h-5 w-5" />
                            کلیدهای API کاربر
                        </CardTitle>
                        <CardDescription>
                            صدور کلید‌های جدید برای دسترسی کلاینتِ کاربر به سرویس‌ها بدون نیاز به پنل. این کلیدها با پیشوند `sk_live_` ایجاد می‌شوند.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {generatedKey && (
                            <Alert className="mb-6 bg-green-50 text-green-900 border-green-200 dark:bg-green-950 dark:text-green-200">
                                <CheckCircle2 className="h-4 w-4" color="#16a34a" />
                                <AlertTitle>کلید ساخته شد</AlertTitle>
                                <AlertDescription className="space-y-2 font-mono">
                                    <p className="text-xs text-current opacity-80 font-sans">لطفاً کلید زیر را کپی کنید، این کلید دیگر نمایش داده نخواهد شد:</p>
                                    <div className="p-3 bg-white dark:bg-black rounded border border-green-300 select-all outline-none break-all">
                                        {generatedKey}
                                    </div>
                                </AlertDescription>
                            </Alert>
                        )}

                        <div className="flex gap-2 max-w-sm mb-6">
                            <Input
                                placeholder="نام توکن (مثلا App Server 1)"
                                value={newKeyName}
                                onChange={e => setNewKeyName(e.target.value)}
                            />
                            <Button onClick={handleCreateApiKey} disabled={isGenerating || !newKeyName.trim()}>
                                <Plus className="h-4 w-4 mr-1" />
                                تولید کلید
                            </Button>
                        </div>

                        <div className="rounded-md border">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>نام کلید</TableHead>
                                        <TableHead>وضعیت</TableHead>
                                        <TableHead>تاریخ ایجاد</TableHead>
                                        <TableHead className="text-left">عملیات</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {apiKeys.length > 0 ? (
                                        apiKeys.map((key) => (
                                            <TableRow key={key.id}>
                                                <TableCell className="font-medium">{key.name}</TableCell>
                                                <TableCell>
                                                    <Badge variant={key.is_active !== false ? "default" : "secondary"}>
                                                        {key.is_active !== false ? "فعال" : "نامعتبر"}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell dir="ltr">{new Date(key.created_at).toLocaleDateString("fa-IR")}</TableCell>
                                                <TableCell className="text-left">
                                                    <Button variant="destructive" size="sm" onClick={() => handleRevokeApiKey(key.id)} disabled={loading || key.is_active === false}>
                                                        <Trash2 className="h-4 w-4 ml-1" />
                                                        ابطال
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    ) : (
                                        <TableRow>
                                            <TableCell colSpan={4} className="text-center py-6 text-gray-500">
                                                هیچ کلید فعالی برای این کاربر یافت نشد.
                                            </TableCell>
                                        </TableRow>
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    </CardContent>
                </Card>
                {/* Audit Logs Section */}
                <Card className="md:col-span-2">
                    <CardHeader>
                        <CardTitle className="text-xl flex items-center gap-2">
                            <Activity className="h-5 w-5 text-purple-500" />
                            تاریخچه ورود (در حال همگام‌سازی)
                        </CardTitle>
                        <CardDescription>
                            این لیست شامل لاگین‌های اخیر است که هنوز به شبکه پاسخ منتقل نشده‌اند.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="rounded-md border">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>عملیات</TableHead>
                                        <TableHead>آی‌پی</TableHead>
                                        <TableHead>وضعیت همگام‌سازی</TableHead>
                                        <TableHead>تاریخ</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {auditLogs.length > 0 ? (
                                        auditLogs.map((log) => (
                                            <TableRow key={log.id}>
                                                <TableCell className="font-medium">{log.action}</TableCell>
                                                <TableCell dir="ltr">{log.ip_address}</TableCell>
                                                <TableCell>
                                                    <Badge variant={log.sync_status === 'pending' ? 'secondary' : 'default'}>
                                                        {log.sync_status}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell dir="ltr">{new Date(log.created_at).toLocaleString("fa-IR")}</TableCell>
                                            </TableRow>
                                        ))
                                    ) : (
                                        <TableRow>
                                            <TableCell colSpan={4} className="text-center py-6 text-gray-500">
                                                لاگ ممیزی در این شبکه یافت نشد (احتمالاً به شبکه پاسخ همگام‌سازی شده‌اند).
                                            </TableCell>
                                        </TableRow>
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
