"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth-store";
import {
    Plus, Search, MoreHorizontal, Edit, Trash2, RefreshCw,
    AlertCircle, FileUp, TestTube2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Switch } from "@/components/ui/switch";
import { Loader2 } from "lucide-react";

import adminApi, {
    FileRequestConfig, FileRequestConfigCreate, FTPProfile,
} from "@/lib/services/admin-api";

export default function FileRequestConfigsPage() {
    const router = useRouter();
    const { user: currentUser, isLoading: authLoading } = useAuthStore();
    const [configs, setConfigs] = useState<FileRequestConfig[]>([]);
    const [ftpProfiles, setFtpProfiles] = useState<FTPProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [dialogOpen, setDialogOpen] = useState(false);
    const [editingConfig, setEditingConfig] = useState<FileRequestConfig | null>(null);
    const [testDialogOpen, setTestDialogOpen] = useState(false);
    const [testJson, setTestJson] = useState("{}");
    const [testParserConfig, setTestParserConfig] = useState("{}");
    const [testResult, setTestResult] = useState<any>(null);

    // Form state
    const [form, setForm] = useState<FileRequestConfigCreate>({
        name: "", display_name: "", description: "",
        send_ftp_profile_id: "", send_path: "/outgoing",
        receive_ftp_profile_id: "", receive_path: "/incoming",
        filename_template: "{request_type}_{timestamp}.json",
        content_format: "json", content_template: undefined,
        content_encoding: "utf-8",
        response_parser_config: undefined,
        response_timeout_minutes: 1440, max_retries: 3,
        poll_interval_seconds: 60, has_error_response: false,
        is_active: true,
    });

    // JSON fields stored as text for editing
    const [contentTemplateText, setContentTemplateText] = useState("");
    const [parserConfigText, setParserConfigText] = useState("");

    useEffect(() => {
        if (!authLoading) {
            fetchConfigs();
            fetchFtpProfiles();
        }
    }, [authLoading]);

    const fetchConfigs = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await adminApi.fileRequestConfigService.getConfigs();
            setConfigs(Array.isArray(data) ? data : []);
        } catch (err) {
            setError("خطا در دریافت لیست پیکربندی‌ها");
        } finally {
            setLoading(false);
        }
    };

    const fetchFtpProfiles = async () => {
        try {
            const data = await adminApi.ftpProfileService.getProfiles();
            setFtpProfiles(Array.isArray(data) ? data : []);
        } catch (err) {
            // Silent — FTP profiles are supplementary
        }
    };

    const getProfileName = (id: string) => {
        const p = ftpProfiles.find((p) => p.id === id);
        return p ? p.display_name : id.substring(0, 8) + "...";
    };

    const openCreateDialog = () => {
        setEditingConfig(null);
        setForm({
            name: "", display_name: "", description: "",
            send_ftp_profile_id: ftpProfiles[0]?.id || "", send_path: "/outgoing",
            receive_ftp_profile_id: ftpProfiles[0]?.id || "", receive_path: "/incoming",
            filename_template: "{request_type}_{timestamp}.json",
            content_format: "json", content_encoding: "utf-8",
            response_timeout_minutes: 1440, max_retries: 3,
            poll_interval_seconds: 60, has_error_response: false, is_active: true,
        });
        setContentTemplateText("");
        setParserConfigText("");
        setDialogOpen(true);
    };

    const openEditDialog = (config: FileRequestConfig) => {
        setEditingConfig(config);
        setForm({
            name: config.name, display_name: config.display_name,
            description: config.description || "",
            send_ftp_profile_id: config.send_ftp_profile_id,
            send_path: config.send_path,
            receive_ftp_profile_id: config.receive_ftp_profile_id,
            receive_path: config.receive_path,
            filename_template: config.filename_template,
            content_format: config.content_format,
            content_encoding: config.content_encoding,
            response_timeout_minutes: config.response_timeout_minutes,
            max_retries: config.max_retries,
            poll_interval_seconds: config.poll_interval_seconds,
            has_error_response: config.has_error_response,
            is_active: config.is_active,
        });
        setContentTemplateText(
            config.content_template ? JSON.stringify(config.content_template, null, 2) : ""
        );
        setParserConfigText(
            config.response_parser_config ? JSON.stringify(config.response_parser_config, null, 2) : ""
        );
        setDialogOpen(true);
    };

    const handleSave = async () => {
        try {
            const saveData: any = { ...form };

            // Parse JSON fields
            if (contentTemplateText.trim()) {
                saveData.content_template = JSON.parse(contentTemplateText);
            } else {
                saveData.content_template = null;
            }
            if (parserConfigText.trim()) {
                saveData.response_parser_config = JSON.parse(parserConfigText);
            } else {
                saveData.response_parser_config = null;
            }

            if (editingConfig) {
                await adminApi.fileRequestConfigService.updateConfig(editingConfig.id, saveData);
            } else {
                await adminApi.fileRequestConfigService.createConfig(saveData);
            }
            setDialogOpen(false);
            fetchConfigs();
        } catch (err: any) {
            if (err instanceof SyntaxError) {
                setError("فرمت JSON نادرست است. لطفاً بررسی کنید.");
            } else {
                setError(err?.response?.data?.detail || "خطا در ذخیره پیکربندی");
            }
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("آیا از حذف این پیکربندی اطمینان دارید؟")) return;
        try {
            await adminApi.fileRequestConfigService.deleteConfig(id);
            fetchConfigs();
        } catch (err) {
            setError("خطا در حذف پیکربندی");
        }
    };

    const handleTestParse = async () => {
        try {
            const sampleJson = JSON.parse(testJson);
            const parserConfig = JSON.parse(testParserConfig);
            const result = await adminApi.fileRequestConfigService.testParse({
                sample_json: sampleJson,
                parser_config: parserConfig,
            });
            setTestResult(result);
        } catch (err: any) {
            if (err instanceof SyntaxError) {
                setTestResult({ success: false, error: "فرمت JSON نادرست" });
            } else {
                setTestResult({ success: false, error: err?.response?.data?.detail || "خطای سرور" });
            }
        }
    };

    const filteredConfigs = configs.filter(
        (c) =>
            c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            c.display_name.toLowerCase().includes(searchTerm.toLowerCase())
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
                                پیکربندی درخواست‌های فایلی
                            </h1>
                            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                تنظیم نحوه تولید فایل درخواست و پارس پاسخ JSON
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={() => setTestDialogOpen(true)}>
                                <TestTube2 className="h-4 w-4 mr-2" />
                                تست پارسر
                            </Button>
                            <Button variant="outline" size="icon" onClick={fetchConfigs} disabled={loading}>
                                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                            </Button>
                            <Button variant="default" onClick={openCreateDialog}>
                                <Plus className="h-4 w-4 mr-2" />
                                پیکربندی جدید
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

                {/* Stats */}
                <div className="grid gap-4 md:grid-cols-3 mb-6">
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-medium">کل پیکربندی‌ها</CardTitle>
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
                            <CardTitle className="text-sm font-medium">با تشخیص خطا</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-3xl font-bold text-amber-600">
                                {configs.filter((c) => c.has_error_response).length}
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
                                placeholder="جستجو بر اساس نام..."
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
                        <CardTitle>لیست پیکربندی‌ها</CardTitle>
                        <CardDescription>{filteredConfigs.length} پیکربندی</CardDescription>
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
                                            <TableHead className="text-center">FTP ارسال</TableHead>
                                            <TableHead className="text-center">FTP دریافت</TableHead>
                                            <TableHead className="text-center">فرمت</TableHead>
                                            <TableHead className="text-center">تایم‌اوت</TableHead>
                                            <TableHead className="text-center">وضعیت</TableHead>
                                            <TableHead className="text-center">عملیات</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {filteredConfigs.length > 0 ? (
                                            filteredConfigs.map((config) => (
                                                <TableRow key={config.id}>
                                                    <TableCell className="font-medium text-right">
                                                        <div>
                                                            <span className="font-mono text-primary text-sm">{config.name}</span>
                                                            <p className="text-xs text-gray-500">{config.display_name}</p>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="text-center text-xs">
                                                        <Badge variant="outline" className="font-mono">
                                                            {getProfileName(config.send_ftp_profile_id)}
                                                        </Badge>
                                                        <p className="text-gray-400 mt-1" dir="ltr">{config.send_path}</p>
                                                    </TableCell>
                                                    <TableCell className="text-center text-xs">
                                                        <Badge variant="outline" className="font-mono">
                                                            {getProfileName(config.receive_ftp_profile_id)}
                                                        </Badge>
                                                        <p className="text-gray-400 mt-1" dir="ltr">{config.receive_path}</p>
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <Badge variant="secondary" className="font-mono text-xs">{config.content_format}</Badge>
                                                    </TableCell>
                                                    <TableCell className="text-center text-sm">
                                                        {config.response_timeout_minutes} دقیقه
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <Badge
                                                            variant={config.is_active ? "default" : "secondary"}
                                                            className={
                                                                config.is_active
                                                                    ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                                                                    : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                                                            }
                                                        >
                                                            {config.is_active ? "فعال" : "غیرفعال"}
                                                        </Badge>
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
                                                                <DropdownMenuItem onClick={() => openEditDialog(config)}>
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
                                                <TableCell colSpan={7} className="text-center py-8">
                                                    <p className="text-muted-foreground">
                                                        هیچ پیکربندی یافت نشد. می‌توانید مورد جدیدی اضافه کنید.
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
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>
                            {editingConfig ? "ویرایش پیکربندی" : "پیکربندی جدید"}
                        </DialogTitle>
                        <DialogDescription>
                            تنظیمات تولید فایل درخواست و پارس پاسخ JSON.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-6 py-4">
                        {/* Basic info */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>نام یکتا</Label>
                                <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="inquiry_1" dir="ltr" />
                            </div>
                            <div className="space-y-2">
                                <Label>نام نمایشی</Label>
                                <Input value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} placeholder="استعلام شماره ۱" />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>توضیحات</Label>
                            <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                        </div>

                        {/* FTP Profiles */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>FTP ارسال</Label>
                                <Select value={form.send_ftp_profile_id} onValueChange={(v) => setForm({ ...form, send_ftp_profile_id: v })}>
                                    <SelectTrigger><SelectValue placeholder="انتخاب..." /></SelectTrigger>
                                    <SelectContent>
                                        {ftpProfiles.map((p) => (
                                            <SelectItem key={p.id} value={p.id}>{p.display_name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <Input value={form.send_path} onChange={(e) => setForm({ ...form, send_path: e.target.value })} placeholder="/outgoing" dir="ltr" className="mt-1" />
                            </div>
                            <div className="space-y-2">
                                <Label>FTP دریافت</Label>
                                <Select value={form.receive_ftp_profile_id} onValueChange={(v) => setForm({ ...form, receive_ftp_profile_id: v })}>
                                    <SelectTrigger><SelectValue placeholder="انتخاب..." /></SelectTrigger>
                                    <SelectContent>
                                        {ftpProfiles.map((p) => (
                                            <SelectItem key={p.id} value={p.id}>{p.display_name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <Input value={form.receive_path} onChange={(e) => setForm({ ...form, receive_path: e.target.value })} placeholder="/incoming" dir="ltr" className="mt-1" />
                            </div>
                        </div>

                        {/* File naming */}
                        <div className="space-y-2">
                            <Label>الگوی نام فایل</Label>
                            <Input value={form.filename_template} onChange={(e) => setForm({ ...form, filename_template: e.target.value })} placeholder="{request_type}_{national_code}_{date}.json" dir="ltr" />
                            <p className="text-xs text-gray-500">
                                متغیرها: {"{request_id}"}, {"{request_type}"}, {"{timestamp}"}, {"{date}"}, {"{uuid}"} + هر کلید پارامتر
                            </p>
                        </div>

                        {/* Content format */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>فرمت محتوا</Label>
                                <Select value={form.content_format} onValueChange={(v) => setForm({ ...form, content_format: v })}>
                                    <SelectTrigger><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="json">JSON</SelectItem>
                                        <SelectItem value="csv">CSV</SelectItem>
                                        <SelectItem value="text">متن ساده</SelectItem>
                                        <SelectItem value="custom_template">قالب سفارشی</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label>انکدینگ</Label>
                                <Input value={form.content_encoding} onChange={(e) => setForm({ ...form, content_encoding: e.target.value })} dir="ltr" />
                            </div>
                        </div>

                        {/* Content template */}
                        <div className="space-y-2">
                            <Label>قالب محتوای درخواست (JSON)</Label>
                            <Textarea
                                value={contentTemplateText}
                                onChange={(e) => setContentTemplateText(e.target.value)}
                                placeholder='{"national_code": "{{national_code}}", "date": "{{date}}"}'
                                className="font-mono text-sm" dir="ltr" rows={4}
                            />
                        </div>

                        {/* Response parser config */}
                        <div className="space-y-2">
                            <Label>تنظیمات پارسر پاسخ (JSON)</Label>
                            <Textarea
                                value={parserConfigText}
                                onChange={(e) => setParserConfigText(e.target.value)}
                                placeholder='{"data_root": "data", "extract_keys": {"name": "fullName"}}'
                                className="font-mono text-sm" dir="ltr" rows={6}
                            />
                            <p className="text-xs text-gray-500">
                                data_root: مسیر داده اصلی | extract_keys: نگاشت کلیدها | error_detection: تشخیص خطا
                            </p>
                        </div>

                        {/* Timeout & retry */}
                        <div className="grid grid-cols-3 gap-4">
                            <div className="space-y-2">
                                <Label>تایم‌اوت (دقیقه)</Label>
                                <Input type="number" value={form.response_timeout_minutes} onChange={(e) => setForm({ ...form, response_timeout_minutes: parseInt(e.target.value) || 1440 })} dir="ltr" />
                            </div>
                            <div className="space-y-2">
                                <Label>حداکثر تلاش</Label>
                                <Input type="number" value={form.max_retries} onChange={(e) => setForm({ ...form, max_retries: parseInt(e.target.value) || 3 })} dir="ltr" />
                            </div>
                            <div className="space-y-2">
                                <Label>فاصله بررسی (ثانیه)</Label>
                                <Input type="number" value={form.poll_interval_seconds} onChange={(e) => setForm({ ...form, poll_interval_seconds: parseInt(e.target.value) || 60 })} dir="ltr" />
                            </div>
                        </div>

                        {/* Switches */}
                        <div className="flex items-center gap-6">
                            <div className="flex items-center gap-2">
                                <Switch checked={form.has_error_response} onCheckedChange={(v) => setForm({ ...form, has_error_response: v })} />
                                <Label>پاسخ خطا دارد</Label>
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
                            {editingConfig ? "ذخیره تغییرات" : "ایجاد پیکربندی"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Test Parser Dialog */}
            <Dialog open={testDialogOpen} onOpenChange={setTestDialogOpen}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>تست پارسر JSON</DialogTitle>
                        <DialogDescription>
                            یک JSON نمونه و تنظیمات پارسر وارد کنید تا نتیجه را ببینید.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>JSON نمونه (پاسخ سیستم مقصد)</Label>
                            <Textarea
                                value={testJson}
                                onChange={(e) => setTestJson(e.target.value)}
                                className="font-mono text-sm" dir="ltr" rows={6}
                                placeholder='{"meta":{"status":"OK"},"data":{"fullName":"علی","age":30}}'
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>تنظیمات پارسر</Label>
                            <Textarea
                                value={testParserConfig}
                                onChange={(e) => setTestParserConfig(e.target.value)}
                                className="font-mono text-sm" dir="ltr" rows={6}
                                placeholder='{"data_root":"data","extract_keys":{"نام":"fullName","سن":"age"}}'
                            />
                        </div>
                        <Button onClick={handleTestParse} className="w-full">
                            <TestTube2 className="h-4 w-4 mr-2" />
                            اجرای تست
                        </Button>

                        {testResult && (
                            <div className="mt-4">
                                <Alert variant={testResult.success ? "default" : "destructive"}>
                                    <AlertTitle>{testResult.success ? "✅ موفق" : "❌ ناموفق"}</AlertTitle>
                                    <AlertDescription>
                                        {testResult.error && <p className="text-red-600">{testResult.error}</p>}
                                        {testResult.extracted_data && (
                                            <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-auto max-h-48" dir="ltr">
                                                {JSON.stringify(testResult.extracted_data, null, 2)}
                                            </pre>
                                        )}
                                    </AlertDescription>
                                </Alert>
                            </div>
                        )}
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setTestDialogOpen(false)}>بستن</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
