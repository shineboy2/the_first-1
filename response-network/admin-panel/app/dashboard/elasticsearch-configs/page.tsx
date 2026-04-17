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

import adminApi, { ElasticsearchConfig } from "@/lib/services/admin-api";
import { CreateElasticsearchConfigDialog } from "@/components/elasticsearch-configs/create-dialog";
import { EditElasticsearchConfigDialog } from "@/components/elasticsearch-configs/edit-dialog";

export default function ElasticsearchConfigsPage() {
    const router = useRouter();
    const { user: currentUser, isLoading: authLoading } = useAuthStore();
    const [configs, setConfigs] = useState<ElasticsearchConfig[]>([]);
    const [activeConfig, setActiveConfig] = useState<ElasticsearchConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState("");

    // Dialog states
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [selectedConfig, setSelectedConfig] = useState<ElasticsearchConfig | null>(null);

    useEffect(() => {
        if (!authLoading) {
            fetchConfigs();
        }
    }, [authLoading]);

    const fetchConfigs = async () => {
        try {
            setLoading(true);
            setError(null);
            const [configsData, activeData] = await Promise.all([
                adminApi.elasticsearchConfigService.getConfigs(),
                adminApi.elasticsearchConfigService.getActiveConfig().catch(() => null)
            ]);
            setConfigs(Array.isArray(configsData) ? configsData : []);
            setActiveConfig(activeData);
        } catch (err) {
            console.error("Error fetching Elasticsearch configs:", err);
            setError("خطا در دریافت لیست تنظیمات Elasticsearch");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("آیا از حذف این تنظیمات اطمینان دارید؟ این عمل قابل بازگشت نیست.")) return;

        try {
            await adminApi.elasticsearchConfigService.deleteConfig(id);
            fetchConfigs();
        } catch (err) {
            console.error("Error deleting config:", err);
            setError("خطا در حذف تنظیمات Elasticsearch");
        }
    };

    const filteredConfigs = configs.filter(
        (config) =>
            config.url.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (config.username && config.username.toLowerCase().includes(searchTerm.toLowerCase()))
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
                                تنظیمات Elasticsearch
                            </h1>
                            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                مدیریت اتصالات و تنظیمات Elasticsearch
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
                {activeConfig && (
                    <Alert className="mb-6 border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950">
                        <CheckCircle2 className="h-4 w-4" />
                        <AlertTitle>تنظیمات فعال</AlertTitle>
                        <AlertDescription>
                            تنظیمات فعلی Elasticsearch: {activeConfig.url}
                            {activeConfig.username && ` (کاربر: ${activeConfig.username})`}
                        </AlertDescription>
                    </Alert>
                )}

                {/* Stats */}
                <div className="grid gap-4 md:grid-cols-3 mb-6">
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">کل تنظیمات</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold">{configs.length}</div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">فعال</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-green-600">
                                {configs.filter((c) => c.is_active).length}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">SSL فعال</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-blue-600">
                                {configs.filter((c) => c.verify_ssl).length}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Search */}
                <Card className="mb-6">
                    <CardHeader>
                        <CardTitle>جستجو</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="relative">
                            <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                            <Input
                                placeholder="جستجو بر اساس URL یا نام کاربری..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="pr-10"
                            />
                        </div>
                    </CardContent>
                </Card>

                {/* Table */}
                <Card>
                    <CardHeader>
                        <CardTitle>لیست تنظیمات Elasticsearch</CardTitle>
                        <CardDescription>{filteredConfigs.length} تنظیمات</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="flex justify-center py-8">
                                <Loader2 className="h-6 w-6 animate-spin" />
                            </div>
                        ) : (
                            <div className="rounded-md border">
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead className="text-right">URL</TableHead>
                                            <TableHead className="text-center">کاربری</TableHead>
                                            <TableHead className="text-center">SSL</TableHead>
                                            <TableHead className="text-center">وضعیت</TableHead>
                                            <TableHead className="text-center">عملیات</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {filteredConfigs.length > 0 ? (
                                            filteredConfigs.map((config) => (
                                                <TableRow key={config.id}>
                                                    <TableCell className="font-medium text-right font-mono text-primary text-sm" dir="ltr">
                                                        {config.url}
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        {config.username ? (
                                                            <Badge variant="outline" className="font-mono text-xs">
                                                                {config.username}
                                                            </Badge>
                                                        ) : (
                                                            <span className="text-gray-400 text-sm">-</span>
                                                        )}
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <Badge
                                                            variant={config.verify_ssl ? "default" : "secondary"}
                                                            className={
                                                                config.verify_ssl
                                                                    ? "bg-green-100 text-green-800 hover:bg-green-100 dark:bg-green-900 dark:text-green-200"
                                                                    : "bg-yellow-100 text-yellow-800 hover:bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-200"
                                                            }
                                                        >
                                                            {config.verify_ssl ? "فعال" : "غیرفعال"}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <Badge
                                                            variant={config.is_active ? "default" : "secondary"}
                                                            className={
                                                                config.is_active
                                                                    ? "bg-green-100 text-green-800 hover:bg-green-100 dark:bg-green-900 dark:text-green-200"
                                                                    : "bg-red-100 text-red-800 hover:bg-red-100 dark:bg-red-900 dark:text-red-200"
                                                            }
                                                        >
                                                            {config.is_active ? "فعال" : "غیرفعال"}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <DropdownMenu>
                                                            <DropdownMenuTrigger asChild>
                                                                <Button variant="ghost" className="h-8 w-8 p-0">
                                                                    <span className="sr-only">باز کردن منو</span>
                                                                    <MoreHorizontal className="h-4 w-4" />
                                                                </Button>
                                                            </DropdownMenuTrigger>
                                                            <DropdownMenuContent align="end">
                                                                <DropdownMenuLabel>عملیات</DropdownMenuLabel>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setSelectedConfig(config);
                                                                    setEditDialogOpen(true);
                                                                }}>
                                                                    <Edit className="ml-2 h-4 w-4" />
                                                                    ویرایش
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator />
                                                                <DropdownMenuItem
                                                                    className="text-red-600 focus:text-red-600"
                                                                    onClick={() => handleDelete(config.id)}
                                                                >
                                                                    <Trash2 className="ml-2 h-4 w-4" />
                                                                    حذف
                                                                </DropdownMenuItem>
                                                            </DropdownMenuContent>
                                                        </DropdownMenu>
                                                    </TableCell>
                                                </TableRow>
                                            ))
                                        ) : (
                                            <TableRow>
                                                <TableCell colSpan={5} className="text-center py-8">
                                                    <p className="text-muted-foreground">
                                                        هیچ تنظیماتی یافت نشد. می‌توانید مورد جدیدی اضافه کنید.
                                                    </p>
                                                </TableCell>
                                            </TableRow>
                                        )}
                                    </TableBody>
                                </Table>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Dialogs */}
            <CreateElasticsearchConfigDialog
                open={createDialogOpen}
                onOpenChange={setCreateDialogOpen}
                onSuccess={fetchConfigs}
            />

            <EditElasticsearchConfigDialog
                open={editDialogOpen}
                onOpenChange={setEditDialogOpen}
                onSuccess={fetchConfigs}
                config={selectedConfig}
            />

        </div>
    );
}