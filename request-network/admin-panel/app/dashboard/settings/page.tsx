"use client";

import { useState, useEffect } from "react";
import { useAuthStore } from "@/lib/stores/auth-store";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw, Save, HardDrive } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import api from "@/app/(auth)/api";

export default function SettingsPage() {
    const { user, isLoading: authLoading } = useAuthStore();
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMsg, setSuccessMsg] = useState<string | null>(null);

    const [activeTab, setActiveTab] = useState("user_import");
    const [config, setConfig] = useState({
        storage_type: "local",
        enabled: false,
        format: "json",
        local_path: "./imports",
        ftp_host: "",
        ftp_port: 21,
        ftp_user: "",
        ftp_password: "",
        ftp_path: "/",
        ftp_use_tls: false,
    });

    const isAdmin = user?.profile_type === "admin" || user?.role === "admin";

    const fetchConfig = async (type: string) => {
        setLoading(true);
        setError(null);
        try {
            const result = await api.get(`/api/v1/admin/imports/config/${type}`);
            if (result.data) {
                setConfig({
                    storage_type: result.data.storage_type || result.data.destination_type || "local",
                    enabled: result.data.enabled || false,
                    format: result.data.format || "json",
                    local_path: result.data.local_path || "./imports",
                    ftp_host: result.data.ftp_host || "",
                    ftp_port: result.data.ftp_port || 21,
                    ftp_user: result.data.ftp_user || "",
                    ftp_password: result.data.ftp_password || "",
                    ftp_path: result.data.ftp_path || "/",
                    ftp_use_tls: result.data.ftp_use_tls || false,
                });
            }
        } catch (err: any) {
            console.error("Error fetching config:", err);
            // Default blank config
            setConfig({
                storage_type: "local",
                enabled: false,
                format: "json",
                local_path: "./imports",
                ftp_host: "",
                ftp_port: 21,
                ftp_user: "",
                ftp_password: "",
                ftp_path: "/",
                ftp_use_tls: false,
            });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isAdmin) {
            fetchConfig(activeTab);
            setSuccessMsg(null);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab, isAdmin]);

    const handleSaveConfig = async () => {
        setSaving(true);
        setError(null);
        setSuccessMsg(null);
        try {
            await api.post(`/api/v1/admin/imports/config/${activeTab}`, {
                destination_type: config.storage_type,
                ...config
            });
            setSuccessMsg("تنظیمات همگام‌سازی با موفقیت ذخیره شد");
        } catch (err: any) {
            console.error("Error saving config:", err);
            setError("خطا در ذخیره تنظیمات");
        } finally {
            setSaving(false);
        }
    };

    const handleTriggerAdminImport = async () => {
        if (!confirm("آیا از اجرای دستور همگام‌سازی کاربری اطمینان دارید؟")) return;
        setLoading(true);
        try {
            await api.post(`/api/v1/settings/system/trigger_import`);
            setSuccessMsg("فرآیند همگام‌سازی کاربر در پس‌زمینه شروع شد");
        } catch (err: any) {
            console.error("Error triggering import:", err);
            setError("خطا در اجرای همگام‌سازی");
        } finally {
            setLoading(false);
        }
    };

    if (authLoading) {
        return <div className="flex h-full items-center justify-center p-8"><Loader2 className="h-8 w-8 animate-spin" /></div>;
    }

    if (!isAdmin) {
        return (
            <div className="p-8">
                <Alert variant="destructive">
                    <AlertTitle>دسترسی غیرمجاز</AlertTitle>
                    <AlertDescription>فقط مدیران سیستم قابلیت مشاهده این صفحه را دارند.</AlertDescription>
                </Alert>
            </div>
        );
    }

    const typeLabels: Record<string, string> = {
        "user_import": "دریافت کاربران (از شبکه پاسخ)",
        "request_export": "ارسال درخواست‌ها (به شبکه پاسخ)",
        "result_import": "دریافت نتایج (از شبکه پاسخ)",
    };

    return (
        <div className="p-8 space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-l from-blue-600 to-indigo-600 bg-clip-text text-transparent">تنظیمات همگام‌سازی اطلاعات</h1>
                    <p className="text-gray-500 mt-2">پیکربندی درگاه‌های عبور داده بین شبکه درخواست و پاسخ از طریق شکاف هوا (FTP/Local)</p>
                </div>
            </div>

            {error && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>خطا</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            {successMsg && (
                <Alert className="bg-green-50 border-green-200">
                    <Save className="h-4 w-4 text-green-600" />
                    <AlertTitle className="text-green-800">موفق</AlertTitle>
                    <AlertDescription className="text-green-700">{successMsg}</AlertDescription>
                </Alert>
            )}

            <div className="flex space-x-2 space-x-reverse mb-6 overflow-x-auto pb-2">
                {Object.keys(typeLabels).map((key) => (
                    <Button
                        key={key}
                        variant={activeTab === key ? "default" : "outline"}
                        onClick={() => setActiveTab(key)}
                        className="whitespace-nowrap"
                    >
                        {typeLabels[key]}
                    </Button>
                ))}
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="text-lg flex items-center justify-between">
                        <span>پیکربندی {typeLabels[activeTab]}</span>
                        <Button variant="outline" size="sm" onClick={() => fetchConfig(activeTab)} disabled={loading}>
                            <RefreshCw className={`w-4 h-4 ml-2 ${loading ? 'animate-spin' : ''}`} />
                            بازخوانی
                        </Button>
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                    {loading ? (
                        <div className="flex justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="flex items-center space-x-2 space-x-reverse bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                <Switch
                                    id="enabled"
                                    checked={config.enabled}
                                    onCheckedChange={(checked) => setConfig({ ...config, enabled: checked })}
                                    className="direction-ltr"
                                />
                                <Label htmlFor="enabled" className="font-bold text-lg">وضعیت همگام‌سازی خودکار در پس‌زمینه (فعال/غیرفعال)</Label>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>فرمت فایل (پسوند)</Label>
                                    <Select value={config.format} onValueChange={(v) => setConfig({ ...config, format: v })}>
                                        <SelectTrigger dir="ltr"><SelectValue /></SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="json">JSON</SelectItem>
                                            <SelectItem value="jsonl">JSON Lines</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>نوع ارتباط انتقال فایل</Label>
                                    <Select value={config.storage_type} onValueChange={(v) => setConfig({ ...config, storage_type: v })}>
                                        <SelectTrigger dir="ltr"><SelectValue /></SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="local">دایرکتوری محلی (Mount Point)</SelectItem>
                                            <SelectItem value="ftp">سرور FTP راه دور</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            {config.storage_type === "local" && (
                                <div className="space-y-2 bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                                    <Label>مسیر دایرکتوری در کانتینر</Label>
                                    <Input
                                        dir="ltr"
                                        className="font-mono text-left bg-white dark:bg-black"
                                        value={config.local_path}
                                        onChange={(e) => setConfig({ ...config, local_path: e.target.value })}
                                    />
                                    <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                                        این مسیر باید در Docker Volume به شکل اشتراکی کانفیگ شده باشد
                                    </p>
                                </div>
                            )}

                            {config.storage_type === "ftp" && (
                                <div className="space-y-4 bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>میزبان (Host IP/Domain)</Label>
                                            <Input dir="ltr" className="font-mono text-left bg-white dark:bg-black" value={config.ftp_host} onChange={(e) => setConfig({ ...config, ftp_host: e.target.value })} />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>پورت FTP</Label>
                                            <Input dir="ltr" type="number" className="font-mono text-left bg-white dark:bg-black" value={config.ftp_port} onChange={(e) => setConfig({ ...config, ftp_port: parseInt(e.target.value) || 21 })} />
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>شناسه کاربری (Username)</Label>
                                            <Input dir="ltr" className="font-mono text-left bg-white dark:bg-black" value={config.ftp_user} onChange={(e) => setConfig({ ...config, ftp_user: e.target.value })} />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>رمز عبور (Password)</Label>
                                            <Input dir="ltr" type="password" className="font-mono text-left bg-white dark:bg-black" value={config.ftp_password} onChange={(e) => setConfig({ ...config, ftp_password: e.target.value })} />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <Label>مسیر در سرور FTP</Label>
                                        <Input dir="ltr" className="font-mono text-left bg-white dark:bg-black" value={config.ftp_path} onChange={(e) => setConfig({ ...config, ftp_path: e.target.value })} />
                                    </div>
                                    <div className="flex items-center space-x-2 space-x-reverse pt-2">
                                        <Switch
                                            id="tls"
                                            checked={config.ftp_use_tls}
                                            onCheckedChange={(checked) => setConfig({ ...config, ftp_use_tls: checked })}
                                            className="direction-ltr"
                                        />
                                        <Label htmlFor="tls">استفاده از پروتکل امن (FTP over TLS)</Label>
                                    </div>
                                </div>
                            )}

                            <Button onClick={handleSaveConfig} disabled={saving} className="w-full mt-4">
                                {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4 ml-2" />}
                                ثبت تنظیمات
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>

            {activeTab === "user_import" && (
                <Card className="border-green-200">
                    <CardHeader className="bg-green-50 dark:bg-green-900/10 border-b border-green-200">
                        <CardTitle className="text-green-800 dark:text-green-400">عملیات دستی ادمین</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-6">
                        <p className="text-sm text-gray-600 mb-4 items-center">
                            شما میتوانید فرآیند درج دستی و همگام‌سازی کاربران را به صورت فوری آغاز کنید. این عملیات در پس‌زمینه توسط Celery اجرا خواهد شد.
                        </p>
                        <Button variant="default" className="bg-green-600 hover:bg-green-700 text-white" onClick={handleTriggerAdminImport} disabled={loading}>
                            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <HardDrive className="mr-2 h-4 w-4 ml-2" />}
                            اجرای یکباره همگام‌سازی کاربران Response Network
                        </Button>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
