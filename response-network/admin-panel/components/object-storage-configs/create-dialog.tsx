"use client";

import { useState } from "react";
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
import adminApi from "@/lib/services/admin-api";
import type { ObjectStorageConfigCreate } from "@/lib/services/admin-api";
import { Textarea } from "@/components/ui/textarea";

interface CreateObjectStorageConfigDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

export function CreateObjectStorageConfigDialog({
    open,
    onOpenChange,
    onSuccess,
}: CreateObjectStorageConfigDialogProps) {
    const [loading, setLoading] = useState(false);
    const [testing, setTesting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

    const [formData, setFormData] = useState<ObjectStorageConfigCreate>({
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

    const resetForm = () => {
        setFormData({
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
        setError(null);
        setTestResult(null);
    };

    const handleTestConnection = async () => {
        setTesting(true);
        setTestResult(null);
        setError(null);

        try {
            const result = await adminApi.objectStorageConfigService.testNewConnection(formData);
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
            await adminApi.objectStorageConfigService.createConfig(formData);
            onSuccess();
            onOpenChange(false);
            resetForm();
        } catch (err: any) {
            console.error("Create Object Storage config error:", err);
            setError(err.response?.data?.detail || err.message || "خطا در ایجاد تنظیمات Object Storage");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={(v) => {
            onOpenChange(v);
            if (!v) resetForm();
        }}>
            <DialogContent className="sm:max-w-[600px] rtl max-h-[90vh] overflow-y-auto">
                <DialogHeader className="text-right">
                    <DialogTitle>ایجاد تنظیمات Object Storage جدید</DialogTitle>
                    <DialogDescription>
                        اطلاعات اتصال به سرویس ذخیره‌سازی شیء (Ceph/MinIO) را وارد کنید.
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
                            <Label htmlFor="name">نام یکتا (انگلیسی)</Label>
                            <Input
                                id="name"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                placeholder="my-ceph-1"
                                required
                                className="text-left"
                                dir="ltr"
                            />
                        </div>

                        <div className="space-y-2 text-right">
                            <Label htmlFor="display_name">نام نمایشی</Label>
                            <Input
                                id="display_name"
                                value={formData.display_name}
                                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                                placeholder="سرور اصلی سف"
                                required
                            />
                        </div>
                    </div>

                    <div className="space-y-2 text-right">
                        <Label htmlFor="endpoint_url">آدرس (Endpoint URL)</Label>
                        <Input
                            id="endpoint_url"
                            type="url"
                            value={formData.endpoint_url}
                            onChange={(e) => setFormData({ ...formData, endpoint_url: e.target.value })}
                            placeholder="http://minio:9000"
                            required
                            className="text-left"
                            dir="ltr"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2 text-right">
                            <Label htmlFor="access_key">Access Key</Label>
                            <Input
                                id="access_key"
                                value={formData.access_key}
                                onChange={(e) => setFormData({ ...formData, access_key: e.target.value })}
                                required
                                className="text-left"
                                dir="ltr"
                            />
                        </div>

                        <div className="space-y-2 text-right">
                            <Label htmlFor="secret_key">Secret Key</Label>
                            <Input
                                id="secret_key"
                                type="password"
                                value={formData.secret_key}
                                onChange={(e) => setFormData({ ...formData, secret_key: e.target.value })}
                                required
                                className="text-left"
                                dir="ltr"
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2 text-right">
                            <Label htmlFor="default_bucket">نام باکت پیش‌فرض</Label>
                            <Input
                                id="default_bucket"
                                value={formData.default_bucket}
                                onChange={(e) => setFormData({ ...formData, default_bucket: e.target.value })}
                                required
                                className="text-left"
                                dir="ltr"
                            />
                        </div>
                        <div className="space-y-2 text-right">
                            <Label htmlFor="storage_type">نوع سرویس</Label>
                            <select
                                id="storage_type"
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
                                id="use_ssl"
                                checked={formData.use_ssl}
                                onCheckedChange={(checked) => setFormData({ ...formData, use_ssl: checked })}
                            />
                            <Label htmlFor="use_ssl">استفاده از SSL/HTTPS</Label>
                        </div>
                        <div className="flex items-center space-x-2 space-x-reverse">
                            <Switch
                                id="path_style"
                                checked={formData.path_style}
                                onCheckedChange={(checked) => setFormData({ ...formData, path_style: checked })}
                            />
                            <Label htmlFor="path_style">استفاده از Path Style (اجباری برای Ceph/MinIO)</Label>
                        </div>
                        <div className="flex items-center space-x-2 space-x-reverse">
                            <Switch
                                id="is_active"
                                checked={formData.is_active}
                                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                            />
                            <Label htmlFor="is_active">فعال‌سازی این پیکربندی</Label>
                        </div>
                    </div>

                    <div className="space-y-2 text-right">
                        <Label htmlFor="description">توضیحات (اختیاری)</Label>
                        <Textarea
                            id="description"
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            placeholder="توضیحاتی درباره این اتصال..."
                            className="text-right"
                        />
                    </div>

                    <div className="flex justify-between pt-4 border-t">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={handleTestConnection}
                            disabled={testing || !formData.endpoint_url || !formData.access_key || !formData.secret_key || !formData.default_bucket}
                        >
                            {testing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                            تست اتصال
                        </Button>

                        <div className="space-x-2 space-x-reverse">
                            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                                انصراف
                            </Button>
                            <Button type="submit" disabled={loading || testing}>
                                {loading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                                ایجاد
                            </Button>
                        </div>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
