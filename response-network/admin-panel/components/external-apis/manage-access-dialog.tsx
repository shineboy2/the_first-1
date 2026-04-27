"use client";

import { useState, useEffect } from "react";
import { Loader2, Trash2, UserPlus, Users, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import adminApi, { ExternalAPI, ProfileType, User } from "@/lib/services/admin-api";

interface ManageAccessDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
    externalApi: ExternalAPI | null;
}

interface ProfileAccess {
    profile_type: string;
    has_access: boolean;
}

interface UserAccess {
    user_id: string;
    username: string;
    email: string;
    full_name: string | null;
    has_access: boolean;
}

export function ManageAccessDialog({
    open,
    onOpenChange,
    onSuccess,
    externalApi,
}: ManageAccessDialogProps) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    
    // Profile Type states
    const [profileTypes, setProfileTypes] = useState<ProfileType[]>([]);
    const [profileAccess, setProfileAccess] = useState<ProfileAccess[]>([]);
    const [selectedProfileType, setSelectedProfileType] = useState<string>("");
    
    // User states
    const [users, setUsers] = useState<User[]>([]);
    const [userAccess, setUserAccess] = useState<UserAccess[]>([]);
    const [selectedUser, setSelectedUser] = useState<string>("");

    useEffect(() => {
        if (open && externalApi) {
            fetchData();
        }
    }, [open, externalApi]);

    const fetchData = async () => {
        if (!externalApi) return;
        
        try {
            setLoading(true);
            setError(null);
            
            // Fetch profile types
            const profileTypesData = await adminApi.profileTypeService.getProfileTypes();
            setProfileTypes(Array.isArray(profileTypesData) ? profileTypesData : []);
            
            // Fetch profile access
            const accessData: ProfileAccess[] = [];
            for (const pt of (Array.isArray(profileTypesData) ? profileTypesData : [])) {
                try {
                    const access = await adminApi.externalApiService.getProfileTypeAccess(pt.name);
                    const hasAccess = access.allowed_external_apis?.includes(externalApi.name) || false;
                    accessData.push({
                        profile_type: pt.name,
                        has_access: hasAccess,
                    });
                } catch (err) {
                    console.error(`Error fetching access for ${pt.name}:`, err);
                    accessData.push({
                        profile_type: pt.name,
                        has_access: false,
                    });
                }
            }
            setProfileAccess(accessData);
            
            // Fetch users
            const usersData = await adminApi.userService.getUsers();
            setUsers(Array.isArray(usersData) ? usersData : []);
            
            // Fetch user access
            const userAccessData = await adminApi.externalApiService.getUserAccess(externalApi.id);
            setUserAccess(userAccessData);
            
        } catch (err) {
            console.error("Error fetching data:", err);
            setError("خطا در دریافت اطلاعات");
        } finally {
            setLoading(false);
        }
    };

    const handleGrantProfileAccess = async () => {
        if (!externalApi || !selectedProfileType) return;

        try {
            setError(null);
            setSuccess(null);
            
            const currentAccess = await adminApi.externalApiService.getProfileTypeAccess(selectedProfileType);
            const currentApis = currentAccess.allowed_external_apis || [];
            
            if (!currentApis.includes(externalApi.name)) {
                const updatedApis = [...currentApis, externalApi.name];
                await adminApi.externalApiService.updateProfileTypeAccess(selectedProfileType, updatedApis);
                
                setSuccess("دسترسی با موفقیت اعطا شد");
                setTimeout(() => setSuccess(null), 3000);
                setSelectedProfileType("");
                await fetchData();
                onSuccess();
            } else {
                setError("این پروفایل از قبل دسترسی دارد");
            }
        } catch (err: any) {
            console.error("Error granting access:", err);
            setError(err.response?.data?.detail || "خطا در اعطای دسترسی");
        }
    };

    const handleRevokeProfileAccess = async (profileType: string) => {
        if (!externalApi) return;

        if (!confirm(`آیا از لغو دسترسی ${profileType} به ${externalApi.name} اطمینان دارید؟`)) {
            return;
        }

        try {
            setError(null);
            setSuccess(null);
            
            const currentAccess = await adminApi.externalApiService.getProfileTypeAccess(profileType);
            const currentApis = currentAccess.allowed_external_apis || [];
            const updatedApis = currentApis.filter(api => api !== externalApi.name);
            await adminApi.externalApiService.updateProfileTypeAccess(profileType, updatedApis);
            
            setSuccess("دسترسی با موفقیت لغو شد");
            setTimeout(() => setSuccess(null), 3000);
            await fetchData();
            onSuccess();
        } catch (err: any) {
            console.error("Error revoking access:", err);
            setError(err.response?.data?.detail || "خطا در لغو دسترسی");
        }
    };

    const handleGrantUserAccess = async () => {
        if (!externalApi || !selectedUser) return;

        try {
            setError(null);
            setSuccess(null);
            
            await adminApi.externalApiService.grantUserAccess(externalApi.id, [selectedUser]);
            
            setSuccess("دسترسی کاربر با موفقیت اعطا شد");
            setTimeout(() => setSuccess(null), 3000);
            setSelectedUser("");
            await fetchData();
            onSuccess();
        } catch (err: any) {
            console.error("Error granting user access:", err);
            setError(err.response?.data?.detail || "خطا در اعطای دسترسی کاربر");
        }
    };

    const handleRevokeUserAccess = async (userId: string) => {
        if (!externalApi) return;

        const user = userAccess.find(u => u.user_id === userId);
        if (!confirm(`آیا از لغو دسترسی ${user?.username} به ${externalApi.name} اطمینان دارید؟`)) {
            return;
        }

        try {
            setError(null);
            setSuccess(null);
            
            await adminApi.externalApiService.revokeUserAccess(externalApi.id, userId);
            
            setSuccess("دسترسی کاربر با موفقیت لغو شد");
            setTimeout(() => setSuccess(null), 3000);
            await fetchData();
            onSuccess();
        } catch (err: any) {
            console.error("Error revoking user access:", err);
            setError(err.response?.data?.detail || "خطا در لغو دسترسی کاربر");
        }
    };

    const availableProfileTypes = profileTypes.filter(pt =>
        !profileAccess.find(pa => pa.profile_type === pt.name && pa.has_access)
    );

    const profileTypesWithAccess = profileAccess.filter(pa => pa.has_access);

    const availableUsers = users.filter(user =>
        !userAccess.some(access => access.user_id === user.id)
    );

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[800px] max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Users className="h-5 w-5" />
                        مدیریت دسترسی
                    </DialogTitle>
                    <DialogDescription>
                        مدیریت دسترسی انواع پروفایل و کاربران به API خارجی: <span className="font-mono font-bold">{externalApi?.name}</span>
                    </DialogDescription>
                </DialogHeader>

                <Tabs defaultValue="profile" className="w-full">
                    <TabsList className="grid w-full grid-cols-2">
                        <TabsTrigger value="profile">
                            <Users className="ml-2 h-4 w-4" />
                            دسترسی پروفایل‌ها
                        </TabsTrigger>
                        <TabsTrigger value="user">
                            <UserPlus className="ml-2 h-4 w-4" />
                            دسترسی کاربران
                        </TabsTrigger>
                    </TabsList>

                    {error && (
                        <Alert variant="destructive" className="mt-4">
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}

                    {success && (
                        <Alert className="mt-4 bg-green-50 text-green-900 border-green-200">
                            <AlertDescription>{success}</AlertDescription>
                        </Alert>
                    )}

                    {/* Profile Type Access Tab */}
                    <TabsContent value="profile" className="space-y-4">
                        <div className="space-y-4 border rounded-lg p-4 bg-muted/50">
                            <h3 className="font-medium text-sm">اضافه کردن دسترسی پروفایل</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                                <div className="space-y-2 md:col-span-2">
                                    <Label className="text-xs">نوع پروفایل</Label>
                                    <Select value={selectedProfileType} onValueChange={setSelectedProfileType}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="انتخاب کنید" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {availableProfileTypes.length > 0 ? (
                                                availableProfileTypes.map((pt) => (
                                                    <SelectItem key={pt.name} value={pt.name}>
                                                        {pt.display_name || pt.name}
                                                    </SelectItem>
                                                ))
                                            ) : (
                                                <div className="p-2 text-xs text-center text-muted-foreground">
                                                    همه پروفایل‌ها دسترسی دارند
                                                </div>
                                            )}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <Button onClick={handleGrantProfileAccess} disabled={!selectedProfileType || loading} className="w-full">
                                    <UserPlus className="mr-2 h-4 w-4" />
                                    افزودن
                                </Button>
                            </div>
                        </div>

                        <div className="border rounded-lg overflow-hidden">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>نوع پروفایل</TableHead>
                                        <TableHead>توضیحات</TableHead>
                                        <TableHead className="text-center">وضعیت</TableHead>
                                        <TableHead className="text-center">عملیات</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {loading ? (
                                        <TableRow>
                                            <TableCell colSpan={4} className="text-center py-8">
                                                <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                                            </TableCell>
                                        </TableRow>
                                    ) : profileTypesWithAccess.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                                                هیچ پروفایلی دسترسی ندارد
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        profileTypesWithAccess.map((access) => {
                                            const profileType = profileTypes.find(pt => pt.name === access.profile_type);
                                            return (
                                                <TableRow key={access.profile_type}>
                                                    <TableCell className="font-medium">
                                                        {profileType?.display_name || access.profile_type}
                                                    </TableCell>
                                                    <TableCell className="text-sm text-muted-foreground">
                                                        {profileType?.description || "-"}
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <Badge variant="default" className="bg-green-100 text-green-800">
                                                            دارای دسترسی
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                                                            onClick={() => handleRevokeProfileAccess(access.profile_type)}
                                                            disabled={loading}
                                                        >
                                                            <Trash2 className="h-4 w-4" />
                                                        </Button>
                                                    </TableCell>
                                                </TableRow>
                                            );
                                        })
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    </TabsContent>

                    {/* User Access Tab */}
                    <TabsContent value="user" className="space-y-4">
                        <div className="space-y-4 border rounded-lg p-4 bg-muted/50">
                            <h3 className="font-medium text-sm">اضافه کردن دسترسی کاربر</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                                <div className="space-y-2 md:col-span-2">
                                    <Label className="text-xs">کاربر</Label>
                                    <Select value={selectedUser} onValueChange={setSelectedUser}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="انتخاب کاربر..." />
                                        </SelectTrigger>
                                        <SelectContent className="max-h-[200px]">
                                            {availableUsers.length > 0 ? (
                                                availableUsers.map((u) => (
                                                    <SelectItem key={u.id} value={u.id}>
                                                        {u.username} ({u.full_name || u.email})
                                                    </SelectItem>
                                                ))
                                            ) : (
                                                <div className="p-2 text-xs text-center text-muted-foreground">
                                                    کاربری یافت نشد
                                                </div>
                                            )}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <Button onClick={handleGrantUserAccess} disabled={!selectedUser || loading} className="w-full">
                                    <UserPlus className="mr-2 h-4 w-4" />
                                    افزودن
                                </Button>
                            </div>
                        </div>

                        <div className="border rounded-lg overflow-hidden">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>نام کاربری</TableHead>
                                        <TableHead>نام کامل</TableHead>
                                        <TableHead>ایمیل</TableHead>
                                        <TableHead className="text-center">عملیات</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {loading ? (
                                        <TableRow>
                                            <TableCell colSpan={4} className="text-center py-8">
                                                <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                                            </TableCell>
                                        </TableRow>
                                    ) : userAccess.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                                                هیچ کاربری دسترسی ندارد
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        userAccess.map((access) => (
                                            <TableRow key={access.user_id}>
                                                <TableCell className="font-medium">{access.username}</TableCell>
                                                <TableCell>{access.full_name || "-"}</TableCell>
                                                <TableCell>{access.email}</TableCell>
                                                <TableCell className="text-center">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                                                        onClick={() => handleRevokeUserAccess(access.user_id)}
                                                        disabled={loading}
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    </TabsContent>
                </Tabs>
            </DialogContent>
        </Dialog>
    );
}
