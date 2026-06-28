"use client";

import { useEffect, useState, Suspense } from "react";
import { useAuthStore } from "@/lib/stores/auth-store";
import { useSearchParams, useRouter } from "next/navigation";
import {
    Activity,
    Loader2,
    Search,
    AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
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

import adminApi, { AuditLog } from "@/lib/services/admin-api";

function AuditLogsContent() {
    const { user: currentUser, isLoading: authLoading } = useAuthStore();
    const searchParams = useSearchParams();
    const router = useRouter();
    
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState(searchParams.get("user_id") || "");
    
    const fetchLogs = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await adminApi.auditLogService.getLogs({ limit: 100 });
            setLogs(data.items || []);
        } catch (err: any) {
            console.error("Error fetching audit logs:", err);
            setError("خطا در دریافت لاگ‌های ممیزی");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!authLoading && currentUser) {
            fetchLogs();
        }
    }, [authLoading, currentUser]);

    const filteredLogs = logs.filter(log => 
        (log.action && log.action.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (log.user_id && log.user_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (log.ip_address && log.ip_address.includes(searchTerm))
    );

    if (authLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    if (!currentUser) return null;

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <div className="border-b bg-white dark:bg-gray-800">
                <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
                    <div className="flex items-center gap-3">
                        <Activity className="h-8 w-8 text-purple-600" />
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                                لاگ‌های ممیزی امنیتی
                            </h1>
                            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                تاریخچه جامع رویدادها که از شبکه درخواست همگام‌سازی شده‌اند.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {error && (
                    <Alert variant="destructive" className="mb-6">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>خطا</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                <Card className="mb-6">
                    <CardHeader>
                        <CardTitle>جستجو</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex gap-2">
                            <div className="flex-1 relative">
                                <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                                <Input
                                    placeholder="جستجو بر اساس اکشن، شناسه کاربر یا IP..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="pr-10"
                                />
                            </div>
                            <Button onClick={fetchLogs} disabled={loading} variant="outline">
                                به‌روزرسانی
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-0">
                        <div className="rounded-md border-0">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>عملیات</TableHead>
                                        <TableHead>آی‌پی</TableHead>
                                        <TableHead>شناسه کاربر</TableHead>
                                        <TableHead>تاریخ</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {loading ? (
                                        <TableRow>
                                            <TableCell colSpan={4} className="text-center py-10">
                                                <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                                            </TableCell>
                                        </TableRow>
                                    ) : filteredLogs.length > 0 ? (
                                        filteredLogs.map((log) => (
                                            <TableRow key={log.id}>
                                                <TableCell>
                                                    <Badge variant={
                                                        log.action.includes('FAILED') ? 'destructive' :
                                                        log.action.includes('SUCCESS') ? 'default' : 'secondary'
                                                    }>
                                                        {log.action}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell dir="ltr" className="text-right font-mono text-sm">
                                                    {log.ip_address || "-"}
                                                </TableCell>
                                                <TableCell dir="ltr" className="text-right text-xs text-muted-foreground">
                                                    {log.user_id || "نامشخص"}
                                                </TableCell>
                                                <TableCell dir="ltr" className="text-right text-sm">
                                                    {new Date(log.created_at).toLocaleString("fa-IR")}
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    ) : (
                                        <TableRow>
                                            <TableCell colSpan={4} className="text-center py-6 text-gray-500">
                                                لاگ ممیزی یافت نشد.
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

export default function AuditLogsPage() {
    return (
        <Suspense fallback={
            <div className="flex min-h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        }>
            <AuditLogsContent />
        </Suspense>
    );
}
