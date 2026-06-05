"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth-store";
import {
    Plus, Search, MoreHorizontal, Edit, Trash2, RefreshCw,
    AlertCircle, Wifi, WifiOff, HardDrive,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
    DropdownMenu, DropdownMenuContent, DropdownMenuItem,
    DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    Dialog, DialogContent, DialogDescription, DialogFooter,
    DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Switch } from "@/components/ui/switch";
import { Loader2 } from "lucide-react";

import adminApi, { FTPProfile, FTPProfileCreate } from "@/lib/services/admin-api";

export default function FTPProfilesPage() {
    const router = useRouter();
    const { user: currentUser, isLoading: authLoading } = useAuthStore();
    const [profiles, setProfiles] = useState<FTPProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [dialogOpen, setDialogOpen] = useState(false);
    const [editingProfile, setEditingProfile] = useState<FTPProfile | null>(null);
    const [testingId, setTestingId] = useState<string | null>(null);
    const [testResult, setTestResult] = useState<string | null>(null);

    // Form state
    const [form, setForm] = useState<FTPProfileCreate>({
        name: "", display_name: "", description: "", host: "",
        port: 21, username: "", password: "", base_path: "/",
        use_tls: false, passive_mode: true, timeout: 30, is_active: true,
    });

    useEffect(() => {
        if (!authLoading) fetchProfiles();
    }, [authLoading]);

    const fetchProfiles = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await adminApi.ftpProfileService.getProfiles();
            setProfiles(Array.isArray(data) ? data : []);
        } catch (err) {
            setError("خطا در دریافت لیست پروفایل‌های FTP");
        } finally {
            setLoading(false);
        }
    };

    const openCreateDialog = () => {
        setEditingProfile(null);
        setForm({
            name: "", display_name: "", description: "", host: "",
            port: 21, username: "", password: "", base_path: "/",
            use_tls: false, passive_mode: true, timeout: 30, is_active: true,
        });
        setDialogOpen(true);
    };

    const openEditDialog = (profile: FTPProfile) => {
        setEditingProfile(profile);
        setForm({
            name: profile.name, display_name: profile.display_name,
            description: profile.description || "", host: profile.host,
            port: profile.port, username: profile.username || "",
            password: "", base_path: profile.base_path,
            use_tls: profile.use_tls, passive_mode: profile.passive_mode,
            timeout: profile.timeout, is_active: profile.is_active,
        });
        setDialogOpen(true);
    };

    const handleSave = async () => {
        try {
            if (editingProfile) {
                const updateData: any = { ...form };
                if (!updateData.password) delete updateData.password;
                await adminApi.ftpProfileService.updateProfile(editingProfile.id, updateData);
            } else {
                await adminApi.ftpProfileService.createProfile(form);
            }
            setDialogOpen(false);
            fetchProfiles();
        } catch (err: any) {
            setError(err?.response?.data?.detail || "خطا در ذخیره پروفایل FTP");
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("آیا از حذف این پروفایل FTP اطمینان دارید؟")) return;
        try {
            await adminApi.ftpProfileService.deleteProfile(id);
            fetchProfiles();
        } catch (err) {
            setError("خطا در حذف پروفایل FTP");
        }
    };

    const handleTestConnection = async (id: string) => {
        setTestingId(id);
        setTestResult(null);
        try {
            const result = await adminApi.ftpProfileService.testConnection(id);
            setTestResult(
                result.success
                    ? `✅ اتصال برقرار شد | خواندن: ${result.can_read ? "✓" : "✗"} | نوشتن: ${result.can_write ? "✓" : "✗"}`
                    : `❌ ${result.message}`
            );
            fetchProfiles(); // Refresh last_tested_at
        } catch (err) {
            setTestResult("❌ خطا در تست اتصال");
        } finally {
            setTestingId(null);
        }
    };

    const filteredProfiles = profiles.filter(
        (p) =>
            p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            p.host.toLowerCase().includes(searchTerm.toLowerCase()) ||
            p.display_name.toLowerCase().includes(searchTerm.toLowerCase())
    );

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
                                پروفایل‌های FTP
                            </h1>
                            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                مدیریت اتصالات FTP برای ارسال/دریافت فایل‌های درخواست
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button variant="outline" size="icon" onClick={fetchProfiles} disabled={loading}>
                                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                            </Button>
                            <Button variant="default" onClick={openCreateDialog}>
                                <Plus className="h-4 w-4 mr-2" />
                                پروفایل جدید
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {error && (
                    <Alert variant="destructive" className="mb-6">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>خطا</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                {testResult && (
                    <Alert className="mb-6">
                        <HardDrive className="h-4 w-4" />
                        <AlertTitle>نتیجه تست اتصال</AlertTitle>
                        <AlertDescription>{testResult}</AlertDescription>
                    </Alert>
                )}

                {/* Stats */}
                <div className="grid gap-4 md:grid-cols-3 mb-6">
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">کل پروفایل‌ها</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold">{profiles.length}</div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">فعال</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-green-600">
                                {profiles.filter((p) => p.is_active).length}
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">غیرفعال</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-red-600">
                                {profiles.filter((p) => !p.is_active).length}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Search */}
                <Card className="mb-6">
                    <CardHeader><CardTitle>جستجو</CardTitle></CardHeader>
                    <CardContent>
                        <div className="relative">
                            <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                            <Input
                                placeholder="جستجو بر اساس نام، هاست..."
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
                        <CardTitle>لیست پروفایل‌های FTP</CardTitle>
                        <CardDescription>{filteredProfiles.length} پروفایل</CardDescription>
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
                                            <TableHead className="text-center">هاست</TableHead>
                                            <TableHead className="text-center">مسیر</TableHead>
                                            <TableHead className="text-center">TLS</TableHead>
                                            <TableHead className="text-center">وضعیت</TableHead>
                                            <TableHead className="text-center">آخرین تست</TableHead>
                                            <TableHead className="text-center">عملیات</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {filteredProfiles.length > 0 ? (
                                            filteredProfiles.map((profile) => (
                                                <TableRow key={profile.id}>
                                                    <TableCell className="font-medium text-right">
                                                        <div>
                                                            <span className="font-mono text-primary text-sm">{profile.name}</span>
                                                            <p className="text-xs text-gray-500">{profile.display_name}</p>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="text-center font-mono text-sm" dir="ltr">
                                                        {profile.host}:{profile.port}
                                                    </TableCell>
                                                    <TableCell className="text-center font-mono text-xs" dir="ltr">
                                                        {profile.base_path}
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        {profile.use_tls ? (
                                                            <Badge variant="default" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">TLS</Badge>
                                                        ) : (
                                                            <Badge variant="secondary">بدون TLS</Badge>
                                                        )}
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <Badge
                                                            variant={profile.is_active ? "default" : "secondary"}
                                                            className={
                                                                profile.is_active
                                                                    ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                                                                    : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                                                            }
                                                        >
                                                            {profile.is_active ? "فعال" : "غیرفعال"}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="text-center text-xs text-gray-500">
                                                        {profile.last_test_result
                                                            ? profile.last_test_result.substring(0, 30)
                                                            : "—"}
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <DropdownMenu>
                                                            <DropdownMenuTrigger asChild>
                                                                <Button variant="ghost" className="h-8 w-8 p-0">
                                                                    <MoreHorizontal className="h-4 w-4" />
                                                                </Button>
                                                            </DropdownMenuTrigger>
                                                            <DropdownMenuContent align="end">
                                                                <DropdownMenuLabel>عملیات</DropdownMenuLabel>
                                                                <DropdownMenuItem onClick={() => handleTestConnection(profile.id)}>
                                                                    <Wifi className="ml-2 h-4 w-4" />
                                                                    تست اتصال
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem onClick={() => openEditDialog(profile)}>
                                                                    <Edit className="ml-2 h-4 w-4" />
                                                                    ویرایش
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator />
                                                                <DropdownMenuItem
                                                                    className="text-red-600 focus:text-red-600"
                                                                    onClick={() => handleDelete(profile.id)}
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
                                                <TableCell colSpan={7} className="text-center py-8">
                                                    <p className="text-muted-foreground">
                                                        هیچ پروفایل FTP یافت نشد. می‌توانید مورد جدیدی اضافه کنید.
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

            {/* Create/Edit Dialog */}
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>
                            {editingProfile ? "ویرایش پروفایل FTP" : "پروفایل FTP جدید"}
                        </DialogTitle>
                        <DialogDescription>
                            مشخصات اتصال FTP را وارد کنید.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>نام یکتا</Label>
                                <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="send_ftp_1" dir="ltr" />
                            </div>
                            <div className="space-y-2">
                                <Label>نام نمایشی</Label>
                                <Input value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} placeholder="FTP ارسال درخواست" />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>توضیحات</Label>
                            <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            <div className="col-span-2 space-y-2">
                                <Label>هاست</Label>
                                <Input value={form.host} onChange={(e) => setForm({ ...form, host: e.target.value })} placeholder="192.168.1.100" dir="ltr" />
                            </div>
                            <div className="space-y-2">
                                <Label>پورت</Label>
                                <Input type="number" value={form.port} onChange={(e) => setForm({ ...form, port: parseInt(e.target.value) || 21 })} dir="ltr" />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>نام کاربری</Label>
                                <Input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} dir="ltr" />
                            </div>
                            <div className="space-y-2">
                                <Label>رمز عبور</Label>
                                <Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} dir="ltr" placeholder={editingProfile ? "(بدون تغییر)" : ""} />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>مسیر پایه</Label>
                            <Input value={form.base_path} onChange={(e) => setForm({ ...form, base_path: e.target.value })} placeholder="/" dir="ltr" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>تایم‌اوت (ثانیه)</Label>
                                <Input type="number" value={form.timeout} onChange={(e) => setForm({ ...form, timeout: parseInt(e.target.value) || 30 })} dir="ltr" />
                            </div>
                        </div>
                        <div className="flex items-center gap-6">
                            <div className="flex items-center gap-2">
                                <Switch checked={form.use_tls} onCheckedChange={(v) => setForm({ ...form, use_tls: v })} />
                                <Label>TLS</Label>
                            </div>
                            <div className="flex items-center gap-2">
                                <Switch checked={form.passive_mode} onCheckedChange={(v) => setForm({ ...form, passive_mode: v })} />
                                <Label>حالت Passive</Label>
                            </div>
                            <div className="flex items-center gap-2">
                                <Switch checked={form.is_active} onCheckedChange={(v) => setForm({ ...form, is_active: v })} />
                                <Label>فعال</Label>
                            </div>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDialogOpen(false)}>انصراف</Button>
                        <Button onClick={handleSave}>
                            {editingProfile ? "ذخیره تغییرات" : "ایجاد پروفایل"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
