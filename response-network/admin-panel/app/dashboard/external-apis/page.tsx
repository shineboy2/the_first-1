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
    Users,
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

import adminApi, { ExternalAPI } from "@/lib/services/admin-api";
import { CreateExternalAPIDialog } from "@/components/external-apis/create-external-api-dialog";
import { EditExternalAPIDialog } from "@/components/external-apis/edit-external-api-dialog";
import { ManageAccessDialog } from "@/components/external-apis/manage-access-dialog";

export default function ExternalAPIsPage() {
    const router = useRouter();
    const { user: currentUser, isLoading: authLoading } = useAuthStore();
    const [apis, setApis] = useState<ExternalAPI[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState("");

    // Dialog states
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [manageAccessDialogOpen, setManageAccessDialogOpen] = useState(false);
    const [selectedApi, setSelectedApi] = useState<ExternalAPI | null>(null);

    useEffect(() => {
        if (!authLoading) {
            fetchExternalAPIs();
        }
    }, [authLoading]);

    const fetchExternalAPIs = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await adminApi.externalApiService.getExternalAPIs();
            setApis(Array.isArray(data) ? data : []);
        } catch (err) {
            console.error("Error fetching external APIs:", err);
            setError("خطا در دریافت لیست API های خارجی");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("آیا از حذف این API اطمینان دارید؟ این عمل قابل بازگشت نیست.")) return;

        try {
            await adminApi.externalApiService.deleteExternalAPI(id);
            fetchExternalAPIs();
        } catch (err) {
            console.error("Error deleting API:", err);
            setError("خطا در حذف API خارجی");
        }
    };

    const filteredApis = apis.filter(
        (api) =>
            api.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            api.endpoint_url.toLowerCase().includes(searchTerm.toLowerCase())
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
                                مدیریت API های خارجی
                            </h1>
                            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                تعریف یکپارچگی‌های سفارشی برای اتصال به سامانه‌های خارجی
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="icon"
                                onClick={fetchExternalAPIs}
                                disabled={loading}
                            >
                                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                            </Button>
                            <Button variant="default" onClick={() => setCreateDialogOpen(true)}>
                                <Plus className="h-4 w-4 mr-2" />
                                افزودن API جدید
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

                {/* Stats */}
                <div className="grid gap-4 md:grid-cols-3 mb-6">
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">کل APIها</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold">{apis.length}</div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">فعال</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-green-600">
                                {apis.filter((a) => a.is_active).length}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">غیرفعال</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-red-600">
                                {apis.filter((a) => !a.is_active).length}
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
                                placeholder="جستجو بر اساس نام یا آدرس مقصد..."
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
                        <CardTitle>لیست اتصالات خارجی</CardTitle>
                        <CardDescription>{filteredApis.length} سامانه پردازشی</CardDescription>
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
                                            <TableHead className="text-right">نام یکتا</TableHead>
                                            <TableHead className="text-left font-mono text-sm leading-tight">URL</TableHead>
                                            <TableHead className="text-center">متد / احراز هویت</TableHead>
                                            <TableHead className="text-center">وضعیت</TableHead>
                                            <TableHead className="text-center">عملیات</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {filteredApis.length > 0 ? (
                                            filteredApis.map((api) => (
                                                <TableRow key={api.id}>
                                                    <TableCell className="font-medium text-right font-mono text-primary text-sm">
                                                        {api.name}
                                                    </TableCell>
                                                    <TableCell className="text-left text-sm text-gray-500 font-mono tracking-tighter" dir="ltr">
                                                        {api.endpoint_url}
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <div className="flex flex-col items-center gap-1">
                                                            <Badge variant="outline" className="font-mono text-xs">{api.http_method}</Badge>
                                                            <Badge variant="secondary" className="text-[10px]">{api.auth_type}</Badge>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <Badge
                                                            variant={api.is_active ? "default" : "secondary"}
                                                            className={
                                                                api.is_active
                                                                    ? "bg-green-100 text-green-800 hover:bg-green-100 dark:bg-green-900 dark:text-green-200"
                                                                    : "bg-red-100 text-red-800 hover:bg-red-100 dark:bg-red-900 dark:text-red-200"
                                                            }
                                                        >
                                                            {api.is_active ? "فعال" : "غیرفعال"}
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
                                                                    setSelectedApi(api);
                                                                    setEditDialogOpen(true);
                                                                }}>
                                                                    <Edit className="ml-2 h-4 w-4" />
                                                                    ویرایش
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setSelectedApi(api);
                                                                    setManageAccessDialogOpen(true);
                                                                }}>
                                                                    <Users className="ml-2 h-4 w-4" />
                                                                    مدیریت دسترسی
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator />
                                                                <DropdownMenuItem
                                                                    className="text-red-600 focus:text-red-600"
                                                                    onClick={() => handleDelete(api.id)}
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
                                                        هیچ API خارجی یافت نشد. می‌توانید مورد جدیدی اضافه کنید.
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
            <CreateExternalAPIDialog
                open={createDialogOpen}
                onOpenChange={setCreateDialogOpen}
                onSuccess={fetchExternalAPIs}
            />

            <EditExternalAPIDialog
                open={editDialogOpen}
                onOpenChange={setEditDialogOpen}
                onSuccess={fetchExternalAPIs}
                apiConfig={selectedApi}
            />

            <ManageAccessDialog
                open={manageAccessDialogOpen}
                onOpenChange={setManageAccessDialogOpen}
                onSuccess={fetchExternalAPIs}
                externalApi={selectedApi}
            />

        </div>
    );
}
