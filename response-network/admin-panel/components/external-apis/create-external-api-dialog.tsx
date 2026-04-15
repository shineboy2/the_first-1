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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Loader2 } from "lucide-react";
import adminApi from "@/lib/services/admin-api";

interface CreateExternalAPIDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

export function CreateExternalAPIDialog({
    open,
    onOpenChange,
    onSuccess,
}: CreateExternalAPIDialogProps) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        name: "",
        description: "",
        endpoint_url: "",
        http_method: "POST",
        auth_type: "none",
        is_active: true,
        auth_config_raw: "",
        static_headers_raw: "",
        payload_template_raw: "",
    });

    const resetForm = () => {
        setFormData({
            name: "",
            description: "",
            endpoint_url: "",
            http_method: "POST",
            auth_type: "none",
            is_active: true,
            auth_config_raw: "",
            static_headers_raw: "",
            payload_template_raw: "",
        });
        setError(null);
    };

    const parseJSON = (jsonString: string, fieldName: string) => {
        if (!jsonString.trim()) return null;
        try {
            return JSON.parse(jsonString);
        } catch {
            throw new Error(`فرمت نامعتبر JSON برای فیلد ${fieldName}`);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const payload = {
                name: formData.name,
                description: formData.description,
                endpoint_url: formData.endpoint_url,
                http_method: formData.http_method,
                auth_type: formData.auth_type,
                is_active: formData.is_active,
                auth_config: parseJSON(formData.auth_config_raw, "پیکربندی احراز هویت"),
                static_headers: parseJSON(formData.static_headers_raw, "هدرهای ایستا"),
                payload_template: parseJSON(formData.payload_template_raw, "قالب Payload"),
            };

            await adminApi.externalApiService.createExternalAPI(payload);
            onSuccess();
            onOpenChange(false);
            resetForm();
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (err: any) {
            console.error("Create external API error:", err);
            setError(err.response?.data?.detail || err.message || "خطا در ایجاد API خارجی");
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
                    <DialogTitle>ایجاد API خارجی جدید</DialogTitle>
                    <DialogDescription>
                        مشخصات API خارجی را برای اتصال به شبکه Response وارد کنید.
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <Alert variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}

                    <div className="space-y-2 text-right">
                        <Label htmlFor="name">نام یکتا (Name)</Label>
                        <Input
                            id="name"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            placeholder="مثال: face_recognition_v1"
                            required
                            className="text-left"
                            dir="ltr"
                        />
                    </div>

                    <div className="space-y-2 text-right">
                        <Label htmlFor="endpoint_url">آدرس مقصد (Endpoint URL)</Label>
                        <Input
                            id="endpoint_url"
                            type="url"
                            value={formData.endpoint_url}
                            onChange={(e) => setFormData({ ...formData, endpoint_url: e.target.value })}
                            placeholder="https://api.example.com/process"
                            required
                            className="text-left"
                            dir="ltr"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2 text-right">
                            <Label htmlFor="http_method">متد HTTP</Label>
                            <Select
                                value={formData.http_method}
                                onValueChange={(v) => setFormData({ ...formData, http_method: v })}
                            >
                                <SelectTrigger dir="ltr">
                                    <SelectValue placeholder="متد" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="POST">POST</SelectItem>
                                    <SelectItem value="GET">GET</SelectItem>
                                    <SelectItem value="PUT">PUT</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2 text-right">
                            <Label htmlFor="auth_type">احراز هویت</Label>
                            <Select
                                value={formData.auth_type}
                                onValueChange={(v) => setFormData({ ...formData, auth_type: v })}
                            >
                                <SelectTrigger dir="ltr">
                                    <SelectValue placeholder="نوع Auth" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="none">بدون احراز هویت (None)</SelectItem>
                                    <SelectItem value="static_key">کلید ایستا (Static Key)</SelectItem>
                                    <SelectItem value="dynamic_token">توکن داینامیک (Dynamic Token)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <div className="space-y-2 text-right">
                        <Label htmlFor="description">توضیحات</Label>
                        <Input
                            id="description"
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            placeholder="توضیحات اختیاری"
                        />
                    </div>

                    {formData.auth_type !== "none" && (
                        <div className="space-y-2 text-right">
                            <Label htmlFor="auth_config_raw">پیکربندی احراز هویت (JSON)</Label>
                            <Textarea
                                id="auth_config_raw"
                                value={formData.auth_config_raw}
                                onChange={(e) => setFormData({ ...formData, auth_config_raw: e.target.value })}
                                placeholder='{"auth_url": "...", "auth_payload": {...}}'
                                className="font-mono text-left"
                                dir="ltr"
                                rows={3}
                            />
                        </div>
                    )}

                    <div className="space-y-2 text-right">
                        <Label htmlFor="static_headers_raw">هدرهای ایستا (JSON)</Label>
                        <Textarea
                            id="static_headers_raw"
                            value={formData.static_headers_raw}
                            onChange={(e) => setFormData({ ...formData, static_headers_raw: e.target.value })}
                            placeholder='{"Content-Type": "application/json"}'
                            className="font-mono text-left"
                            dir="ltr"
                            rows={2}
                        />
                    </div>

                    <div className="space-y-2 text-right">
                        <Label htmlFor="payload_template_raw">قالب Payload (JSON)</Label>
                        <Textarea
                            id="payload_template_raw"
                            value={formData.payload_template_raw}
                            onChange={(e) => setFormData({ ...formData, payload_template_raw: e.target.value })}
                            placeholder='{"image": "{{file_data}}"}'
                            className="font-mono text-left"
                            dir="ltr"
                            rows={4}
                        />
                    </div>

                    <div className="flex items-center space-x-2 space-x-reverse">
                        <Switch
                            id="is_active"
                            checked={formData.is_active}
                            onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                            className="direction-ltr"
                        />
                        <Label htmlFor="is_active">فعال است</Label>
                    </div>

                    <DialogFooter className="sm:justify-start gap-2 mt-4">
                        <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                            انصراف
                        </Button>
                        <Button type="submit" disabled={loading}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            ایجاد سامانه API
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
