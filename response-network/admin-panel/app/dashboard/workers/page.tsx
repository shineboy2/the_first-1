"use client";

import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { RefreshCw, Loader2 } from "lucide-react";
import { adminTasksService, type QueueStats, type WorkerStats, type PendingTask } from "@/lib/services/admin-api";

import { OverviewTab } from "./components/overview-tab";
import { QueueTab } from "./components/queue-tab";
import { SettingsTab } from "./components/settings-tab";

export default function WorkersPage() {
    const [activeTab, setActiveTab] = useState("overview");
    const [loading, setLoading] = useState(true);

    // State
    const [queueStats, setQueueStats] = useState<QueueStats | null>(null);
    const [workerStats, setWorkerStats] = useState<WorkerStats[]>([]);
    const [pendingTasks, setPendingTasks] = useState<PendingTask[]>([]);

    const refreshAll = async () => {
        setLoading(true);
        try {
            const [qStats, wStats, pTasks] = await Promise.all([
                adminTasksService.getQueueStats(),
                adminTasksService.getWorkersStats(),
                adminTasksService.getPendingTasks()
            ]);

            setQueueStats(qStats);
            setWorkerStats(wStats);
            setPendingTasks(pTasks);
        } catch (error) {
            console.error("Error fetching worker data:", error);
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

    return (
        <div className="container mx-auto p-6 space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">مدیریت ورکرها</h1>
                    <p className="text-muted-foreground mt-2">
                        نظارت بر وضعیت صف‌ها، ورکرهای Celery و تنظیمات ذخیره‌سازی
                    </p>
                </div>
                <Button variant="outline" onClick={refreshAll} disabled={loading}>
                    <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                    بروزرسانی
                </Button>
            </div>

            <Tabs defaultValue="overview" value={activeTab} onValueChange={setActiveTab} className="space-y-4">
                <TabsList>
                    <TabsTrigger value="overview">نمای کلی</TabsTrigger>
                    <TabsTrigger value="queue">مدیریت صف</TabsTrigger>
                    <TabsTrigger value="settings">تنظیمات</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4">
                    <OverviewTab queueStats={queueStats} workerStats={workerStats} />
                </TabsContent>

                <TabsContent value="queue" className="space-y-4">
                    <QueueTab tasks={pendingTasks} loading={loading} onRefresh={refreshAll} />
                </TabsContent>

                <TabsContent value="settings" className="space-y-4">
                    <SettingsTab />
                </TabsContent>
            </Tabs>
        </div>
    );
}
