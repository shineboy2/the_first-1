"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Loader2, Trash2, RefreshCw, AlertCircle, PlayCircle, SkipForward } from "lucide-react";
import { adminTasksService, type PendingTask } from "@/lib/services/admin-api";

interface QueueTabProps {
    tasks: PendingTask[];
    loading: boolean;
    onRefresh: () => void;
}

export function QueueTab({ tasks, loading, onRefresh }: QueueTabProps) {
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const handleSkip = async (taskId: string) => {
        try {
            setActionLoading(taskId);
            setError(null);
            await adminTasksService.skipTask(taskId);
            setSuccess(`تسک ${taskId.substring(0, 8)} با موفقیت حذف شد`);
            setTimeout(() => setSuccess(null), 3000);
            onRefresh();
        } catch (err) {
            setError("خطا در حذف تسک");
            console.error(err);
        } finally {
            setActionLoading(null);
        }
    };

    const handleRetry = async (taskId: string) => {
        try {
            setActionLoading(taskId);
            setError(null);
            await adminTasksService.retryTask(taskId);
            setSuccess(`تسک ${taskId.substring(0, 8)} دوباره صف‌بندی شد`);
            setTimeout(() => setSuccess(null), 3000);
            onRefresh();
        } catch (err) {
            setError("خطا در تلاش مجدد تسک");
            console.error(err);
        } finally {
            setActionLoading(null);
        }
    };

    const handleClearQueue = async () => {
        if (!confirm("آیا مطمئن هستید؟ تمام تسک‌های در صف حذف خواهند شد!")) return;

        try {
            setActionLoading("clear-all");
            setError(null);
            await adminTasksService.clearQueue();
            setSuccess("صف با موفقیت پاکسازی شد");
            setTimeout(() => setSuccess(null), 3000);
            onRefresh();
        } catch (err) {
            setError("خطا در پاکسازی صف");
            console.error(err);
        } finally {
            setActionLoading(null);
        }
    };

    return (
        <div className="space-y-6">
            {error && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>خطا</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {success && (
                <Alert className="bg-green-50 text-green-800 border-green-200">
                    <AlertDescription>{success}</AlertDescription>
                </Alert>
            )}

            <div className="flex justify-end">
                <Button
                    variant="destructive"
                    onClick={handleClearQueue}
                    disabled={actionLoading !== null || loading || tasks.length === 0}
                >
                    {actionLoading === "clear-all" ? <Loader2 className="h-4 w-4 animate-spin ml-2" /> : <Trash2 className="h-4 w-4 ml-2" />}
                    خالی کردن کل صف
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>تسک‌های منتظر (Pending)</CardTitle>
                    <CardDescription>لیست تسک‌هایی که در صف انتظار برای اجرا هستند</CardDescription>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="flex justify-center py-8">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : tasks.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                            هیچ تسکی در صف نیست
                        </div>
                    ) : (
                        <div className="rounded-md border">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="text-right">شناسه</TableHead>
                                        <TableHead className="text-right">نام تسک</TableHead>
                                        <TableHead className="text-right">زمان ایجاد</TableHead>
                                        <TableHead className="text-center">عملیات</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {tasks.map((task) => (
                                        <TableRow key={task.id}>
                                            <TableCell className="font-mono text-xs">{task.id}</TableCell>
                                            <TableCell>{task.name}</TableCell>
                                            <TableCell>{task.created_at ? new Date(task.created_at).toLocaleString('fa-IR') : '-'}</TableCell>
                                            <TableCell className="text-center">
                                                <div className="flex justify-center gap-2">
                                                    <Button variant="ghost" size="icon" title="Retry" onClick={() => handleRetry(task.id)} disabled={actionLoading === task.id}>
                                                        <RefreshCw className={`h-4 w-4 ${actionLoading === task.id ? "animate-spin" : ""}`} />
                                                    </Button>
                                                    <Button variant="ghost" size="icon" title="Skip/Delete" onClick={() => handleSkip(task.id)} disabled={actionLoading === task.id}>
                                                        <SkipForward className="h-4 w-4 text-red-500" />
                                                    </Button>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
