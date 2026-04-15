"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, Plus, AlertCircle, Save } from "lucide-react";
import { workerService, type WorkerSettings } from "@/lib/services/admin-api";

export function SettingsTab() {
    const [settings, setSettings] = useState<WorkerSettings[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            setLoading(true);
            const data = await workerService.getWorkerSettings();
            setSettings(data);
        } catch (err) {
            console.error(err);
            setError("خطا در دریافت تنظیمات ورکرها");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                        <CardTitle>تنظیمات ذخیره‌سازی ورکرها</CardTitle>
                        <CardDescription>مدیریت پیکربندی Storage برای ورکرهای مختلف</CardDescription>
                    </div>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="flex justify-center py-8">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : settings.length === 0 ? (
                        <div className="text-center py-12 border-2 border-dashed rounded-lg">
                            <p className="text-muted-foreground mb-4">هیچ تنظیماتی یافت نشد</p>
                            <Button variant="outline" onClick={() => {/* Open Modal */ }}>
                                <Plus className="h-4 w-4 ml-2" />
                                ایجاد تنظیمات جدید
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {settings.map((setting) => (
                                <div key={setting.id} className="border rounded-lg p-4 flex justify-between items-center">
                                    <div>
                                        <h4 className="font-semibold">{setting.name}</h4>
                                        <p className="text-sm text-muted-foreground">Type: {setting.worker_type}</p>
                                    </div>
                                    <div className="flex gap-2">
                                        <Button variant="outline" size="sm">ویرایش</Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>راهنما</AlertTitle>
                <AlertDescription>
                    برای تغییر در زیرساخت ذخیره‌سازی ورکرها (مثلاً تغییر مسیر FTP یا سوئیچ به S3)، از این بخش استفاده کنید.
                    تغییرات پس از ذخیره نیاز به ریستارت سرویس ورکر ندارند.
                </AlertDescription>
            </Alert>
        </div>
    );
}
