"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth-store";
import {
    Plus,
    Search,
    MoreHorizontal,
    Edit,
    Trash2,
    RefreshCw,
    AlertCircle,
    CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2 } from "lucide-react";

import adminApi, { ObjectStorageConfig } from "@/lib/services/admin-api";
import { CreateObjectStorageConfigDialog } from "@/components/object-storage-configs/create-dialog";
import { EditObjectStorageConfigDialog } from "@/components/object-storage-configs/edit-dialog";

export default function ObjectStorageConfigsPage() {
    const router = useRouter();
    const { user: currentUser, isLoading: authLoading } = useAuthStore();
    const [configs, setConfigs] = useState<ObjectStorageConfig[]>([]);
    const [activeConfig, setActiveConfig] = useState<ObjectStorageConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState("");

    // Dialog states
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [selectedConfig, setSelectedConfig] = useState<ObjectStorageConfig | null>(null);

    useEffect(() => {
        if (!authLoading) {
            fetchConfigs();
        }
    }, [authLoading]);

    const fetchConfigs = async () => {
        try {
            setLoading(true);
            setError(null);
            
            // Note: Unlike Elasticsearch which has only one active config concept via getActiveConfig API, 
            // ObjectStorage can have multiple active configs, but we fetch all.
            const configsData = await adminApi.objectStorageConfigService.getConfigs();
            setConfigs(Array.isArray(configsData) ? configsData : []);
            
            // Find active one to highlight if any
            const active = (configsData as ObjectStorageConfig[]).find(c => c.is_active);
            setActiveConfig(active || null);
        } catch (err) {
            console.error("Error fetching Object Storage configs:", err);
            setError("خطا در دریافت لیست تنظیمات Object Storage");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string, isActive: boolean) => {
        if (isActive) {
            alert("نمیتوانید تنظیم فعال را حذف کنید. ابتدا آن را غیرفعال نمایید.");
            return;
        }

        if (!confirm("آیا از حذف این تنظیمات اطمینان دارید؟ این عمل قابل بازگشت نیست.")) return;

        try {
            await adminApi.objectStorageConfigService.deleteConfig(id);
            fetchConfigs();
        } catch (err) {
            console.error("Error deleting config:", err);
            setError("خطا در حذف تنظیمات Object Storage");
        }
    };

    const filteredConfigs = configs.filter(
        (config) =>
            config.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            config.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            config.endpoint_url.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Check auth
    if (authLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    if (!currentUser || currentUser.role !== "admin") {
        router.push("/dashboard");
        return null;
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            {/* Header */}
            <div className="border-b bg-white dark:bg-gray-800">
                <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                                تنظیمات Object Storage
                            </h1>
                            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                مدیریت اتصالات Ceph و MinIO برای دریافت فایل‌ها
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="icon"
                                onClick={fetchConfigs}
                                disabled={loading}
                            >
                                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                            </Button>
                            <Button variant="default" onClick={() => setCreateDialogOpen(true)}>
                                <Plus className="h-4 w-4 mr-2" />
                                افزودن تنظیمات جدید
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {/* Error Alert */}
                {error && (
                    <Alert variant="destructive" className="mb-6">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>خطا</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                {/* Active Config Alert */}
                {!activeConfig && !loading && configs.length > 0 && (
                    <Alert className="mb-6 border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-900/20 dark:text-amber-200">
                        <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                        <AlertTitle>هشدار: تنظیم فعال وجود ندارد</AlertTitle>
                        <AlertDescription>
                            هیچ پیکربندی فعال برای Object Storage وجود ندارد. انواع درخواست‌هایی که از نوع Object Storage هستند کار نخواهند کرد.
                        </AlertDescription>
                    </Alert>
                )}

                <div className="grid gap-6">
                    {/* Configs List Card */}
                    <Card>
                        <CardHeader className="flex flex-col sm:flex-row items-center justify-between space-y-2 sm:space-y-0">
                            <div>
                                <CardTitle>لیست تنظیمات</CardTitle>
                                <CardDescription>
                                    همه تنظیمات ذخیره‌سازی شیء در سیستم
                                </CardDescription>
                            </div>
                            <div className="relative w-full sm:w-64">
                                <Search className="absolute right-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="جستجو بر اساس نام یا آدرس..."
                                    className="pr-8"
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="rounded-md border">
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead className="text-right">نام / نوع</TableHead>
                                            <TableHead className="text-right">آدرس / باکت</TableHead>
                                            <TableHead className="text-right">وضعیت</TableHead>
                                            <TableHead className="text-right">آخرین تست</TableHead>
                                            <TableHead className="text-left">عملیات</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {loading ? (
                                            <TableRow>
                                                <TableCell colSpan={5} className="text-center py-8">
                                                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
                                                </TableCell>
                                            </TableRow>
                                        ) : filteredConfigs.length === 0 ? (
                                            <TableRow>
                                                <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                                                    هیچ تنظیمی یافت نشد
                                                </TableCell>
                                            </TableRow>
                                        ) : (
                                            filteredConfigs.map((config) => (
                                                <TableRow key={config.id}>
                                                    <TableCell>
                                                        <div className="font-medium">{config.display_name}</div>
                                                        <div className="text-sm text-muted-foreground font-mono" dir="ltr">
                                                            {config.name} ({config.storage_type})
                                                        </div>
                                                    </TableCell>
                                                    <TableCell>
                                                        <div className="text-sm font-mono" dir="ltr">{config.endpoint_url}</div>
                                                        <div className="text-sm text-muted-foreground font-mono mt-1" dir="ltr">
                                                            Bucket: {config.default_bucket}
                                                        </div>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Badge variant={config.is_active ? "default" : "secondary"}>
                                                            {config.is_active ? "فعال" : "غیرفعال"}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell>
                                                        {config.last_test_result ? (
                                                            <div className="text-sm">
                                                                <div className={`flex items-center gap-1 ${config.last_test_result.startsWith("OK") ? "text-green-600" : "text-red-600"}`}>
                                                                    {config.last_test_result.startsWith("OK") ? (
                                                                        <CheckCircle2 className="h-3 w-3" />
                                                                    ) : (
                                                                        <AlertCircle className="h-3 w-3" />
                                                                    )}
                                                                    <span className="truncate max-w-[150px]" title={config.last_test_result}>
                                                                        {config.last_test_result}
                                                                    </span>
                                                                </div>
                                                                <div className="text-xs text-muted-foreground mt-1" dir="ltr">
                                                                    {new Date(config.last_tested_at || "").toLocaleString("fa-IR")}
                                                                </div>
                                                            </div>
                                                        ) : (
                                                            <span className="text-sm text-muted-foreground">تست نشده</span>
                                                        )}
                                                    </TableCell>
                                                    <TableCell className="text-left">
                                                        <DropdownMenu>
                                                            <DropdownMenuTrigger asChild>
                                                                <Button variant="ghost" className="h-8 w-8 p-0">
                                                                    <span className="sr-only">باز کردن منو</span>
                                                                    <MoreHorizontal className="h-4 w-4" />
                                                                </Button>
                                                            </DropdownMenuTrigger>
                                                            <DropdownMenuContent align="end">
                                                                <DropdownMenuLabel>عملیات</DropdownMenuLabel>
                                                                <DropdownMenuItem
                                                                    onClick={() => {
                                                                        setSelectedConfig(config);
                                                                        setEditDialogOpen(true);
                                                                    }}
                                                                >
                                                                    <Edit className="h-4 w-4 mr-2" />
                                                                    ویرایش
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator />
                                                                <DropdownMenuItem
                                                                    onClick={() => handleDelete(config.id, config.is_active)}
                                                                    disabled={config.is_active}
                                                                    className={!config.is_active ? "text-red-600" : ""}
                                                                >
                                                                    <Trash2 className="h-4 w-4 mr-2" />
                                                                    حذف
                                                                </DropdownMenuItem>
                                                            </DropdownMenuContent>
                                                        </DropdownMenu>
                                                    </TableCell>
                                                </TableRow>
                                            ))
                                        )}
                                    </TableBody>
                                </Table>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Dialogs */}
            <CreateObjectStorageConfigDialog
                open={createDialogOpen}
                onOpenChange={setCreateDialogOpen}
                onSuccess={fetchConfigs}
            />

            <EditObjectStorageConfigDialog
                config={selectedConfig}
                open={editDialogOpen}
                onOpenChange={setEditDialogOpen}
                onSuccess={fetchConfigs}
            />
        </div>
    );
}
