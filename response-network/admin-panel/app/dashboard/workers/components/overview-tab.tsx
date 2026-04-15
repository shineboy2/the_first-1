"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, Server, Layers } from "lucide-react";
import type { QueueStats, WorkerStats } from "@/lib/services/admin-api";

interface OverviewTabProps {
    queueStats: QueueStats | null;
    workerStats: WorkerStats[];
}

export function OverviewTab({ queueStats, workerStats }: OverviewTabProps) {
    if (!queueStats) return null;

    return (
        <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">تسک‌های در صف</CardTitle>
                        <Layers className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{queueStats.total_queued}</div>
                        <p className="text-xs text-muted-foreground">
                            Waiting in Redis
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">تسک‌های فعال</CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{queueStats.total_active}</div>
                        <p className="text-xs text-muted-foreground">
                            Currently executing
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">ورکرهای فعال</CardTitle>
                        <Server className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{queueStats.active_workers}</div>
                        <p className="text-xs text-muted-foreground">
                            Online worker nodes
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Workers Detailed List */}
            <h3 className="text-xl font-semibold mt-8 mb-4">وضعیت ورکرها</h3>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {workerStats.map((worker) => (
                    <Card key={worker.worker_name} className="overflow-hidden">
                        <CardHeader className="pb-3 bg-muted/20">
                            <div className="flex justify-between items-start">
                                <div>
                                    <CardTitle className="text-base break-all">{worker.worker_name}</CardTitle>
                                    <CardDescription>Pool: {worker.pool_type}</CardDescription>
                                </div>
                                <Badge variant={worker.offline ? "destructive" : "default"}>
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
                                    <span className="font-medium text-blue-600">{worker.active_tasks}</span>
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
        </div>
    );
}
