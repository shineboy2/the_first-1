"use client";

import { useState, useEffect } from "react";
import { useAuthStore } from "@/lib/stores/auth-store";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Loader2, Plus, RefreshCw, Key, Trash2, Copy, AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import adminApi, { APIKey } from "@/lib/services/admin-api";
import { Badge } from "@/components/ui/badge";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog";

export default function ApiKeysPage() {
    const { user, isLoading: authLoading } = useAuthStore();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [newKeyName, setNewKeyName] = useState("");
    const [newKeyHash, setNewKeyHash] = useState<string | null>(null);

    const fetchData = async () => {
        if (!user?.id) return;
        setLoading(true);
        setError(null);
        try {
            const keys = await adminApi.apiKeyService.getUserApiKeys(user.id);
            setApiKeys(keys);
        } catch (err: any) {
            console.error("Error fetching API keys:", err);
            setError(err.response?.data?.detail || "خطا در دریافت لیست توکن‌ها");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (user?.id) {
            fetchData();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.id]);

    const handleCreateKey = async () => {
        if (!newKeyName || !user?.id) return;
        setLoading(true);
        setError(null);
        setNewKeyHash(null);
        try {
            const result = await adminApi.apiKeyService.createUserApiKey(user.id, newKeyName, ["read", "write"]);
            setNewKeyHash(result.api_key || "توکن با موفقیت ایجاد شد ولی نمایش داده نشد");
            await fetchData();
        } catch (err: any) {
            console.error("Error creating API key:", err);
            setError("خطا در ایجاد توکن جدید");
        } finally {
            setLoading(false);
        }
    };

    const handleRevokeKey = async (keyId: string) => {
        if (!user?.id || !confirm("آیا از ابطال این توکن اطمینان دارید؟ برنامه‌های متصل دیگر قادر به استفاده نخواهند بود.")) return;

        try {
            await adminApi.apiKeyService.revokeUserApiKey(user.id, keyId);
            await fetchData();
        } catch (err: any) {
            console.error("Error revoking API key:", err);
            setError("خطا در ابطال توکن");
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        alert("در کلیپ‌بورد کپی شد");
    };

    if (authLoading) {
        return <div className="flex h-full items-center justify-center p-8"><Loader2 className="h-8 w-8 animate-spin" /></div>;
    }

    return (
        <div className="p-8 space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-l from-blue-600 to-indigo-600 bg-clip-text text-transparent">مدیریت توکن‌های دسترسی</h1>
                    <p className="text-gray-500 mt-2">تولید و مدیریت توکن‌های دسترسی برای اتصال برنامه‌های دیگر (API Clients).</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={fetchData} disabled={loading}>
                        <RefreshCw className={`w-4 h-4 ml-2 ${loading ? 'animate-spin' : ''}`} />
                        بروزرسانی
                    </Button>
                    <Button onClick={() => { setNewKeyName(""); setNewKeyHash(null); setCreateDialogOpen(true); }}>
                        <Plus className="w-4 h-4 ml-2" />
                        ثبت توکن جدید
                    </Button>
                </div>
            </div>

            {error && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>خطا</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            <Card>
                <CardHeader>
                    <CardTitle>توکن‌های فعال من</CardTitle>
                    <CardDescription>فقط توکن‌های فعال قابل مشاهده هستند.</CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="text-right">نام توکن</TableHead>
                                <TableHead className="text-right">تاریخ ایجاد</TableHead>
                                <TableHead className="text-right">وضعیت</TableHead>
                                <TableHead className="text-center">عملیات</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {apiKeys.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={4} className="text-center text-gray-500">
                                        هیچ توکنی یافت نشد.
                                    </TableCell>
                                </TableRow>
                            ) : (
                                apiKeys.map((k) => (
                                    <TableRow key={k.id}>
                                        <TableCell className="font-medium text-right font-mono text-primary text-sm">{k.name}</TableCell>
                                        <TableCell className="text-right text-gray-500 text-sm">{new Date(k.created_at).toLocaleString('fa-IR')}</TableCell>
                                        <TableCell className="text-right">
                                            <Badge variant="default" className="bg-green-100 text-green-800">فعال</Badge>
                                        </TableCell>
                                        <TableCell className="text-center">
                                            <Button variant="ghost" className="text-red-500 hover:text-red-700" onClick={() => handleRevokeKey(k.id)}>
                                                <Trash2 className="w-4 h-4 ml-2" />
                                                ابطال
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
                <DialogContent>
                    <DialogHeader className="text-right">
                        <DialogTitle>ایجاد توکن جدید</DialogTitle>
                        <DialogDescription>
                            برای یکپارچه‌سازی سامانه‌ها می‌توانید از این توکن استفاده کنید. توکن فقط یکبار به شما نمایش داده می‌شود.
                        </DialogDescription>
                    </DialogHeader>

                    {!newKeyHash ? (
                        <div className="space-y-4">
                            <Label>نام توکن (اختیاری یا توصیفی)</Label>
                            <Input
                                placeholder="مثلا سیستم مانیتورینگ کارتابل..."
                                value={newKeyName}
                                onChange={(e) => setNewKeyName(e.target.value)}
                            />
                            <DialogFooter className="sm:justify-start">
                                <Button onClick={handleCreateKey} disabled={loading || !newKeyName}>
                                    {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Key className="mr-2 h-4 w-4 ml-2" />}
                                    تولید توکن مجاز
                                </Button>
                            </DialogFooter>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <Alert className="bg-green-50 border-green-200">
                                <AlertTitle className="text-green-800">توکن خود را ذخیره کنید!</AlertTitle>
                                <AlertDescription className="text-green-700 mt-2 font-mono break-all p-4 bg-white rounded border border-green-100 flex items-center justify-between">
                                    <span dir="ltr">{newKeyHash}</span>
                                    <Button size="sm" variant="outline" onClick={() => copyToClipboard(newKeyHash)}>
                                        <Copy className="h-4 w-4" />
                                    </Button>
                                </AlertDescription>
                            </Alert>
                            <DialogFooter className="sm:justify-start">
                                <Button onClick={() => setCreateDialogOpen(false)}>بستن و اتمام</Button>
                            </DialogFooter>
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}
