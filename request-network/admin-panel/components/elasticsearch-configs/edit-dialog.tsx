"use client";

import { useState, useEffect } from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Loader2, CheckCircle2 } from "lucide-react";
import adminApi, { ElasticsearchConfig } from "@/lib/services/admin-api";

interface EditElasticsearchConfigDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
    config: ElasticsearchConfig | null;
}

export function EditElasticsearchConfigDialog({
    open,
    onOpenChange,
    onSuccess,
    config,
}: EditElasticsearchConfigDialogProps) {
    const [loading, setLoading] = useState(false);
    const [testing, setTesting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

    const [formData, setFormData] = useState({
        url: "",
        username: "",
        password: "",
        verify_ssl: true,
        is_active: false,
    });

    useEffect(() => {
        if (config) {
            setFormData({
                url: config.url,
                username: config.username || "",
                password: "", // Don't populate password for security
                verify_ssl: config.verify_ssl,
                is_active: config.is_active,
            });
            setError(null);
            setTestResult(null);
        }
    }, [config]);

    const resetForm = () => {
        setError(null);
        setTestResult(null);
    };

    const handleTestConnection = async () => {
        setTesting(true);
        setTestResult(null);
        setError(null);

        try {
            const testData = {
                url: formData.url,
                username: formData.username || undefined,
                password: formData.password || undefined,
                verify_ssl: formData.verify_ssl,
                is_active: formData.is_active,
            };
            const result = await adminApi.elasticsearchConfigService.testNewConfig(testData);
            setTestResult(result);
        } catch (err: any) {
            console.error("Test connection error:", err);
            setTestResult({ success: false, message: err.response?.data?.detail || err.message || "خطا در تست اتصال" });
        } finally {
            setTesting(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!config) return;

        setLoading(true);
        setError(null);

        try {
            const updateData: any = {
                url: formData.url,
                verify_ssl: formData.verify_ssl,
                is_active: formData.is_active,
            };

            if (formData.username !== (config.username || "")) {
                updateData.username = formData.username;
            }

            if (formData.password) {
                updateData.password = formData.password;
            }

            await adminApi.elasticsearchConfigService.updateConfig(config.id, updateData);
            onSuccess();
            onOpenChange(false);
            resetForm();
        } catch (err: any) {
            console.error("Update Elasticsearch config error:", err);
            setError(err.response?.data?.detail || err.message || "خطا در بروزرسانی تنظیمات Elasticsearch");
        } finally {
            setLoading(false);
        }
    };

    if (!config) return null;

    return (
        <Dialog open={open} onOpenChange={(v) => {
            onOpenChange(v);
            if (!v) resetForm();
        }}>
            <DialogContent className="sm:max-w-[500px] rtl">
                <DialogHeader className="text-right">
                    <DialogTitle>ویرایش تنظیمات Elasticsearch</DialogTitle>
                    <DialogDescription>
                        اطلاعات اتصال به Elasticsearch را بروزرسانی کنید.
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <Alert variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}

                    {testResult && (
                        <Alert variant={testResult.success ? "default" : "destructive"}>
                            {testResult.success ? (
                                <CheckCircle2 className="h-4 w-4" />
                            ) : (
                                <AlertCircle className="h-4 w-4" />
                            )}
                            <AlertDescription>{testResult.message}</AlertDescription>
                        </Alert>
                    )}

                    <div className="space-y-2 text-right">
                        <Label htmlFor="url">آدرس Elasticsearch (URL)</Label>
                        <Input
                            id="url"
                            type="url"
                            value={formData.url}
                            onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                            placeholder="http://localhost:9200"
                            required
                            className="text-left"
                            dir="ltr"
                        />
                    </div>

                    <div className="space-y-2 text-right">
                        <Label htmlFor="username">نام کاربری (اختیاری)</Label>
                        <Input
                            id="username"
                            value={formData.username}
                            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                            placeholder="elastic"
                            className="text-left"
                            dir="ltr"
                        />
                    </div>

                    <div className="space-y-2 text-right">
                        <Label htmlFor="password">رمز عبور جدید (اختیاری)</Label>
                        <Input
                            id="password"
                            type="password"
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            placeholder="رمز عبور جدید (خالی برای عدم تغییر)"
                            className="text-left"
                            dir="ltr"
                        />
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2 space-x-reverse">
                            <Switch
                                id="verify_ssl"
                                checked={formData.verify_ssl}
                                onCheckedChange={(checked) => setFormData({ ...formData, verify_ssl: checked })}
                            />
                            <Label htmlFor="verify_ssl">تأیید SSL</Label>
                        </div>

                        <div className="flex items-center space-x-2 space-x-reverse">
                            <Switch
                                id="is_active"
                                checked={formData.is_active}
                                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                            />
                            <Label htmlFor="is_active">فعال است</Label>
                        </div>
                    </div>

                    <div className="flex gap-2">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={handleTestConnection}
                            disabled={testing || !formData.url}
                            className="flex-1"
                        >
                            {testing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            تست اتصال
                        </Button>
                    </div>

                    <DialogFooter className="sm:justify-start gap-2 mt-4">
                        <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                            انصراف
                        </Button>
                        <Button type="submit" disabled={loading}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            بروزرسانی تنظیمات
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}