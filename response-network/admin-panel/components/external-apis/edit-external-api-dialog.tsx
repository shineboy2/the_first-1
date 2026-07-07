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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Loader2 } from "lucide-react";
import adminApi, { ExternalAPI } from "@/lib/services/admin-api";

interface EditExternalAPIDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
    apiConfig: ExternalAPI | null;
}

export function EditExternalAPIDialog({
    open,
    onOpenChange,
    onSuccess,
    apiConfig
}: EditExternalAPIDialogProps) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        name: "",
        description: "",
        endpoint_url: "",
        http_method: "POST",
        auth_type: "none",
        is_active: true,
        handler_class: "generic",
        auth_config_raw: "",
        static_headers_raw: "",
        payload_template_raw: "",
    });

    useEffect(() => {
        if (apiConfig && open) {
            setFormData({
                name: apiConfig.name,
                description: apiConfig.description || "",
                endpoint_url: apiConfig.endpoint_url,
                http_method: apiConfig.http_method,
                auth_type: apiConfig.auth_type,
                is_active: apiConfig.is_active,
                handler_class: apiConfig.handler_class || "generic",
                auth_config_raw: apiConfig.auth_config ? JSON.stringify(apiConfig.auth_config, null, 2) : "",
                static_headers_raw: apiConfig.static_headers ? JSON.stringify(apiConfig.static_headers, null, 2) : "",
                payload_template_raw: apiConfig.payload_template ? JSON.stringify(apiConfig.payload_template, null, 2) : "",
            });
            setError(null);
        }
    }, [apiConfig, open]);

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
        if (!apiConfig) return;

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
                handler_class: formData.handler_class,
                auth_config: parseJSON(formData.auth_config_raw, "پیکربندی احراز هویت"),
                static_headers: parseJSON(formData.static_headers_raw, "هدرهای ایستا"),
                payload_template: parseJSON(formData.payload_template_raw, "قالب Payload"),
            };

            await adminApi.externalApiService.updateExternalAPI(apiConfig.id, payload);
            onSuccess();
            onOpenChange(false);
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (err: any) {
            console.error("Update external API error:", err);
            setError(err.response?.data?.detail || err.message || "خطا در بروزرسانی API خارجی");
        } finally {
            setLoading(false);
        }
    };

    if (!apiConfig) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] rtl max-h-[90vh] overflow-y-auto">
                <DialogHeader className="text-right">
                    <DialogTitle>ویرایش API خارجی</DialogTitle>
                    <DialogDescription>
                        مشخصات API خارجی را ویرایش کنید.
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
                        <Label htmlFor="handler_class">نوع هندلر پردازشی</Label>
                        <Select
                            value={formData.handler_class}
                            onValueChange={(v) => setFormData({ ...formData, handler_class: v })}
                        >
                            <SelectTrigger dir="ltr">
                                <SelectValue placeholder="نوع پردازش" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="generic">پردازش عمومی (Generic)</SelectItem>
                                <SelectItem value="face_recognition">تشخیص چهره FF.Security</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    {formData.handler_class === "face_recognition" && (
                        <Alert className="bg-blue-50 border-blue-200">
                            <AlertCircle className="h-4 w-4 text-blue-600" />
                            <AlertDescription className="text-blue-800 text-xs text-right mt-1">
                                در این حالت نیازی به تعریف <b>قالب Payload</b> یا <b>متد HTTP</b> ندارید (توسط کد نادیده گرفته می‌شوند). 
                                در بخش <b>پیکربندی احراز هویت</b>، یک JSON حاوی <code>username</code>، <code>password</code>، <code>threshold</code> و <code>limit</code> وارد کنید. 
                                همچنین <b>نوع احراز هویت</b> را روی Static Key قرار دهید.
                            </AlertDescription>
                        </Alert>
                    )}

                    <div className="space-y-2 text-right">
                        <Label htmlFor="description">توضیحات</Label>
                        <Input
                            id="description"
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        />
                    </div>

                    {formData.auth_type !== "none" && (
                        <div className="space-y-2 text-right">
                            <Label htmlFor="auth_config_raw">پیکربندی احراز هویت (JSON)</Label>
                            <Textarea
                                id="auth_config_raw"
                                value={formData.auth_config_raw}
                                onChange={(e) => setFormData({ ...formData, auth_config_raw: e.target.value })}
                                placeholder={formData.handler_class === "face_recognition" 
                                    ? '{\n  "username": "user",\n  "password": "pwd",\n  "threshold": 0.75,\n  "limit": 10\n}' 
                                    : '{"auth_url": "...", "auth_payload": {...}}'}
                                className="font-mono text-left"
                                dir="ltr"
                                rows={4}
                            />
                        </div>
                    )}

                    {formData.handler_class !== "face_recognition" && (
                        <div className="space-y-2 text-right">
                            <Label htmlFor="static_headers_raw">هدرهای ایستا (JSON)</Label>
                            <Textarea
                                id="static_headers_raw"
                                value={formData.static_headers_raw}
                                onChange={(e) => setFormData({ ...formData, static_headers_raw: e.target.value })}
                                className="font-mono text-left"
                                dir="ltr"
                                rows={2}
                            />
                        </div>
                    )}

                    {formData.handler_class !== "face_recognition" && (
                        <div className="space-y-2 text-right">
                            <Label htmlFor="payload_template_raw">قالب Payload (JSON)</Label>
                            <Textarea
                                id="payload_template_raw"
                                value={formData.payload_template_raw}
                                onChange={(e) => setFormData({ ...formData, payload_template_raw: e.target.value })}
                                className="font-mono text-left"
                                dir="ltr"
                                rows={4}
                            />
                        </div>
                    )}

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
                            بروزرسانی API
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
