"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, RefreshCw, AlertCircle, Save, TestTube, Server, Upload, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import {
    storageConfigService,
    type StorageConfig,
    type OperationType,
    OPERATION_LABELS
} from "@/lib/services/admin-api";

const OPERATION_ICONS: Record<OperationType, typeof Upload> = {
    user_export: Upload,
    request_types_export: Upload,
    result_export: Upload,
    request_import: Download,
};

interface ConfigCardProps {
    operationType: OperationType;
    config: StorageConfig;
    onSave: (operationType: OperationType, config: Partial<StorageConfig>) => Promise<void>;
    onTest: (operationType: OperationType) => Promise<void>;
    onTestConnection: (operationType: OperationType) => Promise<void>;
    saving: boolean;
    testing: boolean;
    testingConnection: boolean;
}

function ConfigCard({ operationType, config, onSave, onTest, onTestConnection, saving, testing, testingConnection }: ConfigCardProps) {
    const [localConfig, setLocalConfig] = useState<StorageConfig>(config);
    const Icon = OPERATION_ICONS[operationType];
    const labels = OPERATION_LABELS[operationType];

    useEffect(() => {
        setLocalConfig(config);
    }, [config]);

    const handleSave = async () => {
        await onSave(operationType, localConfig);
    };

    return (
        <Card className="border-2 hover:border-primary/50 transition-colors">
            <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-primary/10">
                            <Icon className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                            <CardTitle className="text-lg">{labels.title}</CardTitle>
                            <CardDescription>{labels.description}</CardDescription>
                        </div>
                    </div>
                    <Badge variant={localConfig.enabled ? "default" : "secondary"}>
                        {localConfig.enabled ? "فعال" : "غیرفعال"}
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Enable/Disable */}
                <div className="flex items-center justify-between py-2 border-b">
                    <Label htmlFor={`${operationType}-enabled`}>فعال‌سازی</Label>
                    <Switch
                        id={`${operationType}-enabled`}
                        checked={localConfig.enabled}
                        onCheckedChange={(checked) =>
                            setLocalConfig({ ...localConfig, enabled: checked })
                        }
                    />
                </div>

                {/* Format */}
                <div className="space-y-2">
                    <Label>فرمت</Label>
                    <select
                        className="w-full rounded-md border border-input bg-background px-3 py-2"
                        value={localConfig.format || "json"}
                        onChange={(e) => setLocalConfig({ ...localConfig, format: e.target.value })}
                    >
                        <option value="json">JSON</option>
                        <option value="csv">CSV</option>
                    </select>
                </div>

                {/* Destination Type */}
                <div className="space-y-2">
                    <Label>نوع {operationType.includes("export") ? "مقصد" : "منبع"}</Label>
                    <select
                        className="w-full rounded-md border border-input bg-background px-3 py-2"
                        value={localConfig.destination_type || "local"}
                        onChange={(e) => setLocalConfig({
                            ...localConfig,
                            destination_type: e.target.value as 'local' | 'ftp'
                        })}
                    >
                        <option value="local">محلی (Local)</option>
                        <option value="ftp">FTP</option>
                    </select>
                </div>

                {/* Local Config */}
                {localConfig.destination_type === 'local' && (
                    <div className="space-y-2 p-4 rounded-lg bg-muted/50 border">
                        <Label>مسیر محلی</Label>
                        <Input
                            value={localConfig.local_path || ''}
                            onChange={(e) => setLocalConfig({ ...localConfig, local_path: e.target.value })}
                            placeholder="./exports"
                            dir="ltr"
                        />
                    </div>
                )}

                {/* FTP Config */}
                {localConfig.destination_type === 'ftp' && (
                    <div className="space-y-4 p-4 rounded-lg bg-muted/50 border">
                        <div className="flex items-center gap-2 mb-2">
                            <Server className="h-4 w-4" />
                            <span className="font-medium text-sm">تنظیمات FTP</span>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <Label>آدرس سرور</Label>
                                <Input
                                    value={localConfig.ftp_host || ''}
                                    onChange={(e) => setLocalConfig({ ...localConfig, ftp_host: e.target.value })}
                                    placeholder="192.168.214.139"
                                    dir="ltr"
                                />
                            </div>
                            <div>
                                <Label>پورت</Label>
                                <Input
                                    type="number"
                                    value={localConfig.ftp_port || 21}
                                    onChange={(e) => setLocalConfig({ ...localConfig, ftp_port: parseInt(e.target.value) })}
                                    placeholder="21"
                                    dir="ltr"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <Label>نام کاربری</Label>
                                <Input
                                    value={localConfig.ftp_user || ''}
                                    onChange={(e) => setLocalConfig({ ...localConfig, ftp_user: e.target.value })}
                                    placeholder="ftp_user"
                                    dir="ltr"
                                />
                            </div>
                            <div>
                                <Label>رمز عبور</Label>
                                <Input
                                    type="password"
                                    value={localConfig.ftp_password || ''}
                                    onChange={(e) => setLocalConfig({ ...localConfig, ftp_password: e.target.value })}
                                    placeholder="••••••••"
                                    dir="ltr"
                                />
                            </div>
                        </div>

                        <div>
                            <Label>مسیر روی سرور</Label>
                            <Input
                                value={localConfig.ftp_path || ''}
                                onChange={(e) => setLocalConfig({ ...localConfig, ftp_path: e.target.value })}
                                placeholder="users"
                                dir="ltr"
                            />
                        </div>

                        <div className="flex items-center gap-2">
                            <Switch
                                id={`${operationType}-tls`}
                                checked={localConfig.ftp_use_tls || false}
                                onCheckedChange={(checked) => setLocalConfig({ ...localConfig, ftp_use_tls: checked })}
                            />
                            <Label htmlFor={`${operationType}-tls`}>استفاده از TLS/SSL</Label>
                        </div>
                    </div>
                )}

                {/* Actions */}
                <div className="flex flex-col gap-2 pt-4 border-t">
                    <div className="flex gap-2">
                        <Button onClick={handleSave} disabled={saving} className="flex-1">
                            {saving ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : (
                                <Save className="h-4 w-4 mr-2" />
                            )}
                            ذخیره
                        </Button>
                        <Button
                            variant="secondary"
                            onClick={() => onTestConnection(operationType)}
                            disabled={testingConnection}
                        >
                            {testingConnection ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : (
                                <Server className="h-4 w-4 mr-2" />
                            )}
                            تست اتصال
                        </Button>
                    </div>
                    <Button
                        variant="outline"
                        onClick={() => onTest(operationType)}
                        disabled={testing || !localConfig.enabled}
                        className="w-full"
                    >
                        {testing ? (
                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        ) : (
                            <TestTube className="h-4 w-4 mr-2" />
                        )}
                        اجرای عملیات واقعی
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}

export default function StorageSettingsPage() {
    const router = useRouter();
    const [configs, setConfigs] = useState<StorageConfig[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [saving, setSaving] = useState<OperationType | null>(null);
    const [testing, setTesting] = useState<OperationType | null>(null);
    const [testingConnection, setTestingConnection] = useState<OperationType | null>(null);

    useEffect(() => {
        fetchConfigs();
    }, []);

    const fetchConfigs = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await storageConfigService.getAllConfigs();
            setConfigs(Array.isArray(data) ? data : []);
        } catch (err) {
            console.error("Error fetching configs:", err);
            setError("خطا در دریافت تنظیمات");
            // Set default empty configs
            setConfigs([
                { operation_type: 'user_export', enabled: false, format: 'json', destination_type: 'local', configured: false },
                { operation_type: 'result_export', enabled: false, format: 'json', destination_type: 'local', configured: false },
                { operation_type: 'request_import', enabled: false, format: 'json', destination_type: 'local', configured: false },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (operationType: OperationType, config: Partial<StorageConfig>) => {
        try {
            setSaving(operationType);
            setError(null);
            await storageConfigService.updateConfig(operationType, config);
            setSuccess(`تنظیمات ${OPERATION_LABELS[operationType].title} با موفقیت ذخیره شد`);
            setTimeout(() => setSuccess(null), 3000);
            await fetchConfigs();
        } catch (err) {
            console.error("Error saving config:", err);
            setError("خطا در ذخیره تنظیمات");
        } finally {
            setSaving(null);
        }
    };

    const handleTest = async (operationType: OperationType) => {
        try {
            setTesting(operationType);
            setError(null);
            const result = await storageConfigService.testOperation(operationType);
            if (result.success) {
                setSuccess(`تست ${OPERATION_LABELS[operationType].title} با موفقیت انجام شد`);
            } else {
                setError(result.message || "تست ناموفق بود");
            }
            setTimeout(() => setSuccess(null), 3000);
        } catch (err) {
            console.error("Error testing operation:", err);
            setError("خطا در تست عملیات");
        } finally {
            setTesting(null);
        }
    };

    const handleTestConnection = async (operationType: OperationType) => {
        try {
            setTestingConnection(operationType);
            setError(null);
            const result = await storageConfigService.testConnection(operationType);
            if (result.success) {
                setSuccess(`اتصال ${OPERATION_LABELS[operationType].title} برقرار است: ${result.message}`);
            } else {
                setError(`خطا در اتصال: ${result.message}`);
            }
            setTimeout(() => setSuccess(null), 5000);
        } catch (err) {
            console.error("Error testing connection:", err);
            setError("خطا در تست اتصال");
        } finally {
            setTestingConnection(null);
        }
    };

    const getConfig = (operationType: OperationType): StorageConfig => {
        return configs.find(c => c.operation_type === operationType) || {
            operation_type: operationType,
            enabled: false,
            format: 'json',
            destination_type: 'local',
            configured: false,
        };
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <div className="border-b bg-white dark:bg-gray-800">
                <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="icon" onClick={() => router.back()}>
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                        <div className="flex-1">
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                                تنظیمات Storage
                            </h1>
                            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                پیکربندی ذخیره‌سازی برای همه عملیات Import/Export
                            </p>
                        </div>
                        <Button variant="outline" size="icon" onClick={fetchConfigs} disabled={loading}>
                            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                        </Button>
                    </div>
                </div>
            </div>

            <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {error && (
                    <Alert variant="destructive" className="mb-6">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>خطا</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                {success && (
                    <Alert className="mb-6 bg-green-50 text-green-800 border-green-200">
                        <AlertDescription>{success}</AlertDescription>
                    </Alert>
                )}

                {loading ? (
                    <div className="flex justify-center py-16">
                        <Loader2 className="h-8 w-8 animate-spin" />
                    </div>
                ) : (
                    <Tabs defaultValue="user_export" className="w-full">
                        <TabsList className="grid w-full grid-cols-4 mb-8">
                            <TabsTrigger value="user_export" className="flex items-center gap-2">
                                <Upload className="h-4 w-4" />
                                خروجی کاربران
                            </TabsTrigger>
                            <TabsTrigger value="request_types_export" className="flex items-center gap-2">
                                <Upload className="h-4 w-4" />
                                خروجی انواع درخواست
                            </TabsTrigger>
                            <TabsTrigger value="result_export" className="flex items-center gap-2">
                                <Upload className="h-4 w-4" />
                                خروجی نتایج
                            </TabsTrigger>
                            <TabsTrigger value="request_import" className="flex items-center gap-2">
                                <Download className="h-4 w-4" />
                                ورودی درخواست‌ها
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="user_export">
                            <ConfigCard
                                operationType="user_export"
                                config={getConfig('user_export')}
                                onSave={handleSave}
                                onTest={handleTest}
                                onTestConnection={handleTestConnection}
                                saving={saving === 'user_export'}
                                testing={testing === 'user_export'}
                                testingConnection={testingConnection === 'user_export'}
                            />
                        </TabsContent>

                        <TabsContent value="request_types_export">
                            <ConfigCard
                                operationType="request_types_export"
                                config={getConfig('request_types_export')}
                                onSave={handleSave}
                                onTest={handleTest}
                                onTestConnection={handleTestConnection}
                                saving={saving === 'request_types_export'}
                                testing={testing === 'request_types_export'}
                                testingConnection={testingConnection === 'request_types_export'}
                            />
                        </TabsContent>

                        <TabsContent value="result_export">
                            <ConfigCard
                                operationType="result_export"
                                config={getConfig('result_export')}
                                onSave={handleSave}
                                onTest={handleTest}
                                onTestConnection={handleTestConnection}
                                saving={saving === 'result_export'}
                                testing={testing === 'result_export'}
                                testingConnection={testingConnection === 'result_export'}
                            />
                        </TabsContent>

                        <TabsContent value="request_import">
                            <ConfigCard
                                operationType="request_import"
                                config={getConfig('request_import')}
                                onSave={handleSave}
                                onTest={handleTest}
                                onTestConnection={handleTestConnection}
                                saving={saving === 'request_import'}
                                testing={testing === 'request_import'}
                                testingConnection={testingConnection === 'request_import'}
                            />
                        </TabsContent>
                    </Tabs>
                )}

                <Alert className="mt-8">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>نکته</AlertTitle>
                    <AlertDescription>
                        هر عملیات می‌تواند FTP مجزا داشته باشد. برای مثال، خروجی کاربران به یک سرور FTP و ورودی درخواست‌ها از سرور دیگری.
                    </AlertDescription>
                </Alert>
            </div>
        </div>
    );
}
