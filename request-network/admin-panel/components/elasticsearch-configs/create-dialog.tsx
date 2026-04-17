"use client";

import { useState } from "react";
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
import adminApi from "@/lib/services/admin-api";

interface CreateElasticsearchConfigDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

export function CreateElasticsearchConfigDialog({
    open,
    onOpenChange,
    onSuccess,
}: CreateElasticsearchConfigDialogProps) {
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

    const resetForm = () => {
        setFormData({
            url: "",
            username: "",
            password: "",
            verify_ssl: true,
            is_active: false,
        });
        setError(null);
        setTestResult(null);
    };

    const handleTestConnection = async () => {
        setTesting(true);
        setTestResult(null);
        setError(null);

        try {
            const result = await adminApi.elasticsearchConfigService.testNewConfig(formData);
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
        setLoading(true);
        setError(null);

        try {
            await adminApi.elasticsearchConfigService.createConfig(formData);
            onSuccess();
            onOpenChange(false);
            resetForm();
        } catch (err: any) {
            console.error("Create Elasticsearch config error:", err);
            setError(err.response?.data?.detail || err.message || "خطا در ایجاد تنظیمات Elasticsearch");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={(v) => {
            onOpenChange(v);
            if (!v) resetForm();
        }}>
            <DialogContent className="sm:max-w-[500px] rtl">
                <DialogHeader className="text-right">
                    <DialogTitle>ایجاد تنظیمات Elasticsearch جدید</DialogTitle>
                    <DialogDescription>
                        اطلاعات اتصال به Elasticsearch را وارد کنید.
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
                        <Label htmlFor="password">رمز عبور (اختیاری)</Label>
                        <Input
                            id="password"
                            type="password"
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            placeholder="رمز عبور"
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
                            ایجاد تنظیمات
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}