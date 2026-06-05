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
    Settings,
    Code,
    Users,
    RefreshCw,
    AlertCircle,
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

import { requestService, type RequestType } from "@/lib/services/admin-api";
import { CreateRequestTypeDialog } from "@/components/request-types/create-request-type-dialog";
import { EditRequestTypeDialog } from "@/components/request-types/edit-request-type-dialog";
import { ConfigureParametersDialog } from "@/components/request-types/configure-parameters-dialog";
import { ConfigureQueryDialog } from "@/components/request-types/configure-query-dialog";
import { ManageAccessDialog } from "@/components/request-types/manage-access-dialog";
import { ProfileTypeLimitsDialog } from "@/components/request-types/profile-type-limits-dialog";

export default function RequestTypesPage() {
    const router = useRouter();
    const { user: currentUser, isLoading: authLoading } = useAuthStore();
    const [requestTypes, setRequestTypes] = useState<RequestType[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState("");

    // Dialog states
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [configureParamsDialogOpen, setConfigureParamsDialogOpen] = useState(false);
    const [configureQueryDialogOpen, setConfigureQueryDialogOpen] = useState(false);
    const [manageAccessDialogOpen, setManageAccessDialogOpen] = useState(false);
    const [selectedRequestType, setSelectedRequestType] = useState<RequestType | null>(null);
    const [profileTypeLimitsDialogOpen, setProfileTypeLimitsDialogOpen] = useState(false);

    useEffect(() => {
        if (!authLoading) {
            fetchRequestTypes();
        }
    }, [authLoading]);

    const fetchRequestTypes = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await requestService.getRequestTypes();
            setRequestTypes(Array.isArray(data) ? data : []);
        } catch (err) {
            console.error("Error fetching request types:", err);
            setError("خطا در دریافت لیست انواع درخواست");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("آیا از حذف این نوع درخواست اطمینان دارید؟")) return;

        try {
            await requestService.deleteRequestType(id);
            fetchRequestTypes();
        } catch (err) {
            console.error("Error deleting request type:", err);
            setError("خطا در حذف نوع درخواست");
        }
    };

    const filteredRequestTypes = requestTypes.filter(
        (rt) =>
            rt.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (rt.description && rt.description.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    // Check auth
    if (authLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    if (!currentUser) {
        router.push("/login");
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
                                مدیریت انواع درخواست
                            </h1>
                            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                تعریف و مدیریت انواع درخواست‌های سیستم
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="icon"
                                onClick={fetchRequestTypes}
                                disabled={loading}
                            >
                                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                            </Button>
                            <Button variant="default" onClick={() => setCreateDialogOpen(true)}>
                                <Plus className="h-4 w-4 mr-2" />
                                ایجاد نوع درخواست
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
                            <CardTitle className="text-sm font-medium">کل انواع درخواست</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold">{requestTypes.length}</div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">فعال</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-green-600">
                                {requestTypes.filter((rt) => rt.is_active).length}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">غیرفعال</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-red-600">
                                {requestTypes.filter((rt) => !rt.is_active).length}
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
                                placeholder="جستجو بر اساس نام یا توضیحات..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="pr-10"
                            />
                        </div>
                    </CardContent>
                </Card>

                {/* Request Types Table */}
                <Card>
                    <CardHeader>
                        <CardTitle>لیست انواع درخواست</CardTitle>
                        <CardDescription>{filteredRequestTypes.length} نوع درخواست</CardDescription>
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
                                            <TableHead className="text-right">نام</TableHead>
                                            <TableHead className="text-right">توضیحات</TableHead>
                                            <TableHead className="text-center">روش اجرا</TableHead>
                                            <TableHead className="text-center">وضعیت</TableHead>
                                            <TableHead className="text-center">تاریخ ایجاد</TableHead>
                                            <TableHead className="text-center">عملیات</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {filteredRequestTypes.length > 0 ? (
                                            filteredRequestTypes.map((rt) => (
                                                <TableRow key={rt.id}>
                                                    <TableCell className="font-medium">{rt.name}</TableCell>
                                                    <TableCell>{rt.description || "-"}</TableCell>
                                                    <TableCell className="text-center">
                                                        <Badge
                                                            variant="outline"
                                                            className={
                                                                (rt as any).execution_method === "file_request"
                                                                    ? "border-purple-300 text-purple-700 dark:border-purple-600 dark:text-purple-300"
                                                                    : (rt as any).execution_method === "external_api"
                                                                        ? "border-blue-300 text-blue-700 dark:border-blue-600 dark:text-blue-300"
                                                                        : "border-gray-300 text-gray-700 dark:border-gray-600 dark:text-gray-300"
                                                            }
                                                        >
                                                            {(rt as any).execution_method === "file_request"
                                                                ? "درخواست فایلی"
                                                                : (rt as any).execution_method === "external_api"
                                                                    ? "API خارجی"
                                                                    : "Elasticsearch"}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <Badge
                                                            variant={rt.is_active ? "default" : "secondary"}
                                                            className={
                                                                rt.is_active
                                                                    ? "bg-green-100 text-green-800 hover:bg-green-100 dark:bg-green-900 dark:text-green-200"
                                                                    : "bg-red-100 text-red-800 hover:bg-red-100 dark:bg-red-900 dark:text-red-200"
                                                            }
                                                        >
                                                            {rt.is_active ? "فعال" : "غیرفعال"}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="text-center" dir="ltr">
                                                        <span className="text-sm text-muted-foreground">
                                                            {new Date(rt.created_at).toLocaleDateString("fa-IR")}
                                                        </span>
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
                                                                    setSelectedRequestType(rt);
                                                                    setEditDialogOpen(true);
                                                                }}>
                                                                    <Edit className="ml-2 h-4 w-4" />
                                                                    ویرایش
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setSelectedRequestType(rt);
                                                                    setConfigureParamsDialogOpen(true);
                                                                }}>
                                                                    <Settings className="ml-2 h-4 w-4" />
                                                                    تنظیم پارامترها
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setSelectedRequestType(rt);
                                                                    setConfigureQueryDialogOpen(true);
                                                                }}>
                                                                    <Code className="ml-2 h-4 w-4" />
                                                                    تنظیم کوئری
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => {
                                                                    setSelectedRequestType(rt);
                                                                    setManageAccessDialogOpen(true);
                                                                }}>
                                                                    <Users className="ml-2 h-4 w-4" />
                                                                    مدیریت دسترسی
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator />
                                                                <DropdownMenuItem
                                                                    className="text-red-600 focus:text-red-600"
                                                                    onClick={() => handleDelete(rt.id)}
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
                                                <TableCell colSpan={6} className="text-center py-8">
                                                    <p className="text-muted-foreground">
                                                        هیچ نوع درخواستی یافت نشد
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
            <CreateRequestTypeDialog
                open={createDialogOpen}
                onOpenChange={setCreateDialogOpen}
                onSuccess={fetchRequestTypes}
            />

            <EditRequestTypeDialog
                open={editDialogOpen}
                onOpenChange={setEditDialogOpen}
                onSuccess={fetchRequestTypes}
                requestType={selectedRequestType}
            />

            <ConfigureParametersDialog
                open={configureParamsDialogOpen}
                onOpenChange={setConfigureParamsDialogOpen}
                onSuccess={fetchRequestTypes}
                requestType={selectedRequestType}
            />

            <ConfigureQueryDialog
                open={configureQueryDialogOpen}
                onOpenChange={setConfigureQueryDialogOpen}
                onSuccess={fetchRequestTypes}
                requestType={selectedRequestType}
            />

            <ManageAccessDialog
                open={manageAccessDialogOpen}
                onOpenChange={setManageAccessDialogOpen}
                onSuccess={fetchRequestTypes}
                requestType={selectedRequestType}
            />
        </div>
    );
}
