"use client";

import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { RefreshCw, Loader2, PlayCircle, Clock, CheckCircle2, XCircle, Settings2, History } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { adminTasksService, celerySchedulesService, type QueueStats, type WorkerStats, type PendingTask, type CelerySchedule } from "@/lib/services/admin-api";

export default function BackgroundJobsPage() {
    const [activeTab, setActiveTab] = useState("schedules");
    const [loading, setLoading] = useState(true);

    // State
    const [queueStats, setQueueStats] = useState<QueueStats | null>(null);
    const [workerStats, setWorkerStats] = useState<WorkerStats[]>([]);
    const [pendingTasks, setPendingTasks] = useState<PendingTask[]>([]);
    const [schedules, setSchedules] = useState<CelerySchedule[]>([]);

    const refreshAll = async () => {
        setLoading(true);
        try {
            const [qStats, wStats, pTasks, scheds] = await Promise.all([
                adminTasksService.getQueueStats(),
                adminTasksService.getWorkersStats(),
                adminTasksService.getPendingTasks(),
                celerySchedulesService.getSchedules()
            ]);

            setQueueStats(qStats);
            setWorkerStats(wStats);
            setPendingTasks(pTasks);
            setSchedules(scheds);
        } catch (error) {
            console.error("Error fetching background jobs data:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refreshAll();
        // Auto refresh every 10 seconds
        const interval = setInterval(refreshAll, 10000);
        return () => clearInterval(interval);
    }, []);

    const handleUpdateSchedule = async (name: string, intervalSeconds: number) => {
        try {
            await celerySchedulesService.updateSchedule(name, intervalSeconds);
            refreshAll();
        } catch (err) {
            console.error("Error updating schedule", err);
            alert("خطا در بروزرسانی زمان‌بندی");
        }
    };

    return (
        <div className="container mx-auto p-6 space-y-8 animate-in fade-in duration-500">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">وضعیت پردازش‌ها (Background Jobs)</h1>
                    <p className="text-muted-foreground mt-2">
                        مدیریت زمان‌بندی تسک‌ها، همگام‌سازی و مشاهده وضعیت صف‌ها
                    </p>
                </div>
                <Button variant="outline" onClick={refreshAll} disabled={loading}>
                    <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                    بروزرسانی
                </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <Card className="bg-gradient-to-br from-background to-secondary/20">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">تسک‌های در صف</CardTitle>
                        <History className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold">{queueStats?.default_queue_length || 0}</div>
                        <p className="text-xs text-muted-foreground mt-1">Pending in Redis</p>
                    </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-background to-secondary/20">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">تسک‌های زمان‌بندی شده</CardTitle>
                        <Clock className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold">{schedules.length}</div>
                        <p className="text-xs text-muted-foreground mt-1">Active Celery Beat Schedules</p>
                    </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-background to-secondary/20">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">وضعیت ورکرها</CardTitle>
                        <PlayCircle className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold">{workerStats.filter(w => !w.offline).length}</div>
                        <p className="text-xs text-muted-foreground mt-1">Online workers out of {workerStats.length}</p>
                    </CardContent>
                </Card>
            </div>

            <Tabs defaultValue="schedules" value={activeTab} onValueChange={setActiveTab} className="space-y-4">
                <TabsList className="grid w-full grid-cols-3 lg:w-[600px]">
                    <TabsTrigger value="schedules">زمان‌بندی تسک‌ها</TabsTrigger>
                    <TabsTrigger value="queue">صف عملیات</TabsTrigger>
                    <TabsTrigger value="workers">جزئیات ورکرها</TabsTrigger>
                </TabsList>

                <TabsContent value="schedules" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>مدیریت زمان‌بندی (Celery Beat)</CardTitle>
                            <CardDescription>
                                در این بخش می‌توانید دوره‌های تناوب همگام‌سازی و تسک‌های خودکار را تنظیم کنید
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {schedules.map(schedule => (
                                    <div key={schedule.name} className="flex flex-col md:flex-row items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                                        <div className="flex flex-col gap-1 w-full md:w-auto">
                                            <span className="font-semibold text-lg">{schedule.name}</span>
                                            <span className="text-sm text-muted-foreground font-mono bg-muted px-2 py-1 rounded w-fit">{schedule.task}</span>
                                        </div>
                                        <div className="flex items-center gap-4 mt-4 md:mt-0 w-full md:w-auto">
                                            <div className="flex flex-col text-sm text-muted-foreground">
                                                <span>تناوب (ثانیه)</span>
                                            </div>
                                            <input 
                                                type="number" 
                                                className="flex h-10 w-24 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                                defaultValue={schedule.interval || 0}
                                                onBlur={(e) => {
                                                    const val = parseInt(e.target.value);
                                                    if (val !== schedule.interval && val > 0) {
                                                        handleUpdateSchedule(schedule.name, val);
                                                    }
                                                }}
                                            />
                                            <Badge variant={schedule.enabled ? "default" : "secondary"}>
                                                {schedule.enabled ? "فعال" : "غیرفعال"}
                                            </Badge>
                                        </div>
                                    </div>
                                ))}
                                {schedules.length === 0 && !loading && (
                                    <div className="text-center py-8 text-muted-foreground">
                                        هیچ زمان‌بندی یافت نشد.
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="queue" className="space-y-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                                <CardTitle>تسک‌های در حال انتظار</CardTitle>
                                <CardDescription>فهرست تسک‌هایی که در صف قرار دارند</CardDescription>
                            </div>
                            <Button variant="destructive" size="sm" onClick={async () => {
                                if (window.confirm("آیا از حذف تمام تسک‌های صف اطمینان دارید؟ این عمل غیر قابل بازگشت است.")) {
                                    await adminTasksService.clearQueue();
                                    refreshAll();
                                }
                            }}>
                                پاکسازی کل صف
                            </Button>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {pendingTasks.map((task) => (
                                    <div key={task.id} className="border p-4 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                        <div>
                                            <h4 className="font-medium flex items-center gap-2">
                                                <History className="h-4 w-4" />
                                                {task.name}
                                            </h4>
                                            <div className="text-sm text-muted-foreground mt-1 flex gap-4">
                                                <span>ID: {task.id.slice(0, 8)}...</span>
                                                <span>Created: {new Date(task.created_at).toLocaleString('fa-IR')}</span>
                                            </div>
                                        </div>
                                        <Button variant="outline" size="sm" onClick={() => adminTasksService.skipTask(task.id)}>
                                            <XCircle className="h-4 w-4 ml-2" />
                                            لغو تسک
                                        </Button>
                                    </div>
                                ))}
                                {pendingTasks.length === 0 && !loading && (
                                    <div className="text-center py-8 text-muted-foreground border border-dashed rounded-lg">
                                        صف خالی است
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="workers" className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {workerStats.map((worker) => (
                            <Card key={worker.worker_name} className="overflow-hidden">
                                <CardHeader className={`pb-3 ${worker.offline ? 'bg-destructive/10' : 'bg-primary/5'}`}>
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <CardTitle className="text-base break-all">{worker.worker_name.split('@')[1] || worker.worker_name}</CardTitle>
                                            <CardDescription className="mt-1">Node: {worker.worker_name.split('@')[0] || 'celery'}</CardDescription>
                                        </div>
                                        <Badge variant={worker.offline ? "destructive" : "default"} className={!worker.offline ? "bg-green-500" : ""}>
                                            {worker.offline ? "Offline" : "Online"}
                                        </Badge>
                                    </div>
                                </CardHeader>
                                <CardContent className="pt-4">
                                    <div className="space-y-3">
                                        <div className="flex justify-between text-sm">
                                            <span className="text-muted-foreground">Concurrency:</span>
                                            <span className="font-medium">{worker.max_concurrency}</span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                            <span className="text-muted-foreground">Active Tasks:</span>
                                            <span className="font-medium text-blue-600 dark:text-blue-400">{worker.active_tasks}</span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                            <span className="text-muted-foreground">Processed:</span>
                                            <span className="font-medium">{worker.processed_tasks}</span>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
}
