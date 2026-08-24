"use client";

import { useState, useEffect } from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Loader2, CheckCircle2 } from "lucide-react";
import { adminApi, ObjectStorageConfig, ObjectStorageConfigUpdate } from "@/lib/services/admin-api";
import { Textarea } from "@/components/ui/textarea";

interface EditObjectStorageConfigDialogProps {
    config: ObjectStorageConfig | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

export function EditObjectStorageConfigDialog({
    config,
    open,
    onOpenChange,
    onSuccess,
}: EditObjectStorageConfigDialogProps) {
    const [loading, setLoading] = useState(false);
    const [testing, setTesting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

    const [formData, setFormData] = useState<ObjectStorageConfigUpdate>({
        name: "",
        display_name: "",
        description: "",
        storage_type: "minio",
        endpoint_url: "",
        access_key: "",
        secret_key: "",
        region: "us-east-1",
        default_bucket: "",
        use_ssl: false,
        verify_ssl: false,
        path_style: true,
        timeout: 30,
        is_active: false,
    });

    useEffect(() => {
        if (config && open) {
            setFormData({
                name: config.name,
                display_name: config.display_name,
                description: config.description || "",
                storage_type: config.storage_type,
                endpoint_url: config.endpoint_url,
                access_key: config.access_key,
                secret_key: "", // Don't show existing secret key
                region: config.region,
                default_bucket: config.default_bucket,
                use_ssl: config.use_ssl,
                verify_ssl: config.verify_ssl,
                path_style: config.path_style,
                timeout: config.timeout,
                is_active: config.is_active,
            });
            setError(null);
            setTestResult(null);
        }
    }, [config, open]);

    const handleTestConnection = async () => {
        if (!config) return;
        setTesting(true);
        setTestResult(null);
        setError(null);

        try {
            // First we must save if they changed anything, but for simple test we just use existing config ID
            // If they changed the secret_key, they must save it first to test it securely using the ID
            const result = await adminApi.objectStorageConfigService.testConnection(config.id);
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
            // Clean empty secret_key so it doesn't overwrite
            const dataToSubmit = { ...formData };
            if (!dataToSubmit.secret_key) {
                delete dataToSubmit.secret_key;
            }

            await adminApi.objectStorageConfigService.updateConfig(config.id, dataToSubmit);
            onSuccess();
            onOpenChange(false);
        } catch (err: any) {
            console.error("Update Object Storage config error:", err);
            setError(err.response?.data?.detail || err.message || "خطا در بروزرسانی تنظیمات");
        } finally {
            setLoading(false);
        }
    };

    if (!config) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] rtl max-h-[90vh] overflow-y-auto">
                <DialogHeader className="text-right">
                    <DialogTitle>ویرایش تنظیمات Object Storage</DialogTitle>
                    <DialogDescription>
                        ویرایش اطلاعات اتصال {config.name}
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

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2 text-right">
                            <Label htmlFor="edit-name">نام یکتا (انگلیسی)</Label>
                            <Input
                                id="edit-name"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                required
                                className="text-left"
                                dir="ltr"
                            />
                        </div>

                        <div className="space-y-2 text-right">
                            <Label htmlFor="edit-display_name">نام نمایشی</Label>
                            <Input
                                id="edit-display_name"
                                value={formData.display_name}
                                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                                required
                            />
                        </div>
                    </div>

                    <div className="space-y-2 text-right">
                        <Label htmlFor="edit-endpoint_url">آدرس (Endpoint URL)</Label>
                        <Input
                            id="edit-endpoint_url"
                            type="url"
                            value={formData.endpoint_url}
                            onChange={(e) => setFormData({ ...formData, endpoint_url: e.target.value })}
                            required
                            className="text-left"
                            dir="ltr"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2 text-right">
                            <Label htmlFor="edit-access_key">Access Key</Label>
                            <Input
                                id="edit-access_key"
                                value={formData.access_key}
                                onChange={(e) => setFormData({ ...formData, access_key: e.target.value })}
                                required
                                className="text-left"
                                dir="ltr"
                            />
                        </div>

                        <div className="space-y-2 text-right">
                            <Label htmlFor="edit-secret_key">Secret Key (جدید)</Label>
                            <Input
                                id="edit-secret_key"
                                type="password"
                                value={formData.secret_key}
                                onChange={(e) => setFormData({ ...formData, secret_key: e.target.value })}
                                placeholder="فقط در صورت نیاز به تغییر وارد کنید"
                                className="text-left"
                                dir="ltr"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2 text-right">
                            <Label htmlFor="edit-default_bucket">نام باکت پیش‌فرض</Label>
                            <Input
                                id="edit-default_bucket"
                                value={formData.default_bucket}
                                onChange={(e) => setFormData({ ...formData, default_bucket: e.target.value })}
                                required
                                className="text-left"
                                dir="ltr"
                            />
                        </div>
                        <div className="space-y-2 text-right">
                            <Label htmlFor="edit-storage_type">نوع سرویس</Label>
                            <select
                                id="edit-storage_type"
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                                value={formData.storage_type}
                                onChange={(e) => setFormData({ ...formData, storage_type: e.target.value })}
                            >
                                <option value="minio">MinIO</option>
                                <option value="ceph">Ceph</option>
                                <option value="s3">AWS S3</option>
                            </select>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="flex items-center space-x-2 space-x-reverse">
                            <Switch
                                id="edit-use_ssl"
                                checked={formData.use_ssl}
                                onCheckedChange={(checked) => setFormData({ ...formData, use_ssl: checked })}
                            />
                            <Label htmlFor="edit-use_ssl">استفاده از SSL/HTTPS</Label>
                        </div>
                        <div className="flex items-center space-x-2 space-x-reverse">
                            <Switch
                                id="edit-path_style"
                                checked={formData.path_style}
                                onCheckedChange={(checked) => setFormData({ ...formData, path_style: checked })}
                            />
                            <Label htmlFor="edit-path_style">استفاده از Path Style (اجباری برای Ceph/MinIO)</Label>
                        </div>
                        <div className="flex items-center space-x-2 space-x-reverse">
                            <Switch
                                id="edit-is_active"
                                checked={formData.is_active}
                                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                            />
                            <Label htmlFor="edit-is_active">فعال‌سازی این پیکربندی</Label>
                        </div>
                    </div>

                    <div className="space-y-2 text-right">
                        <Label htmlFor="edit-description">توضیحات (اختیاری)</Label>
                        <Textarea
                            id="edit-description"
                            value={formData.description || ""}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            className="text-right"
                        />
                    </div>

                    <div className="flex justify-between pt-4 border-t">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={handleTestConnection}
                            disabled={testing}
                        >
                            {testing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                            تست اتصال (براساس مقادیر ذخیره‌شده)
                        </Button>

                        <div className="space-x-2 space-x-reverse">
                            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                                انصراف
                            </Button>
                            <Button type="submit" disabled={loading || testing}>
                                {loading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                                ذخیره تغییرات
                            </Button>
                        </div>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
