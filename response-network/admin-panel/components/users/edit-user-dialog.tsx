"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Loader2 } from "lucide-react";
import { userService, profileTypeService } from "@/lib/services/admin-api";
import type { User, ProfileType } from "@/lib/services/admin-api";

const editUserSchema = z.object({
    email: z.string().email("ایمیل معتبر وارد کنید").optional(),
    full_name: z.string().min(1, "نام کامل الزامی است").optional(),
    profile_type: z.string().min(1, "نوع پروفایل الزامی است").optional(),
    daily_request_limit: z.number().min(1).optional(),
    monthly_request_limit: z.number().min(1).optional(),
    is_active: z.boolean().optional(),
});

type EditUserFormData = z.infer<typeof editUserSchema>;

interface EditUserDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
    user: User | null;
}

export function EditUserDialog({
    open,
    onOpenChange,
    onSuccess,
    user,
}: EditUserDialogProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [profileTypes, setProfileTypes] = useState<ProfileType[]>([]);
    const [loadingProfileTypes, setLoadingProfileTypes] = useState(false);

    const form = useForm<EditUserFormData>({
        resolver: zodResolver(editUserSchema),
        defaultValues: {
            email: "",
            full_name: "",
            profile_type: "user",
            daily_request_limit: 1000,
            monthly_request_limit: 10000,
            is_active: true,
        },
    });

    useEffect(() => {
        const fetchProfileTypes = async () => {
            try {
                setLoadingProfileTypes(true);
                const types = await profileTypeService.getProfileTypes();
                setProfileTypes(types);
            } catch (error) {
                console.error("Error fetching profile types:", error);
            } finally {
                setLoadingProfileTypes(false);
            }
        };
        fetchProfileTypes();
    }, []);

    useEffect(() => {
        if (user) {
            form.reset({
                email: user.email,
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                full_name: (user as any).full_name || "",
                profile_type: (user.profile_type || user.role || "user"),
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                daily_request_limit: (user as any).daily_request_limit || 1000,
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                monthly_request_limit: (user as any).monthly_request_limit || 10000,
                is_active: user.is_active,
            });
        }
    }, [user, form]);

    const onSubmit = async (data: EditUserFormData) => {
        if (!user) return;

        try {
            setIsLoading(true);
            await userService.updateUser(user.id, data);
            onSuccess();
            onOpenChange(false);
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (error: any) {
            console.error("Error updating user:", error);
            form.setError("root", {
                message: error.response?.data?.detail || "خطا در ویرایش کاربر",
            });
        } finally {
            setIsLoading(false);
        }
    };

    if (!user) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>ویرایش کاربر</DialogTitle>
                    <DialogDescription>
                        ویرایش اطلاعات کاربر: {user.username}
                    </DialogDescription>
                </DialogHeader>

                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                        {form.formState.errors.root && (
                            <div className="text-sm text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded">
                                {form.formState.errors.root.message}
                            </div>
                        )}

                        <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded">
                            <p className="text-sm">
                                <span className="font-medium">نام کاربری:</span> {user.username}
                            </p>
                            <p className="text-sm mt-2">
                                <span className="font-medium">شناسه کاربر (UUID):</span> <span className="font-mono text-xs select-all">{user.id}</span>
                            </p>
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                                نام کاربری و شناسه قابل تغییر نیستند
                            </p>
                        </div>

                        <FormField
                            control={form.control}
                            name="email"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>ایمیل</FormLabel>
                                    <FormControl>
                                        <Input type="email" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="full_name"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>نام کامل</FormLabel>
                                    <FormControl>
                                        <Input {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="profile_type"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>نوع کاربر</FormLabel>
                                    <Select
                                        onValueChange={field.onChange}
                                        value={field.value}
                                    >
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="انتخاب کنید" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            {loadingProfileTypes ? (
                                                <div className="flex justify-center p-2">
                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                </div>
                                            ) : profileTypes.length > 0 ? (
                                                profileTypes.map((pt) => {
                                                    // Ensure we handle the hardcoded types gracefully if they exist in DB or not
                                                    // or just render what we get.
                                                    // Prioritize display_name if available.
                                                    return (
                                                        <SelectItem key={pt.name} value={pt.name}>
                                                            {pt.display_name || pt.name}
                                                        </SelectItem>
                                                    );
                                                })
                                            ) : (
                                                <>
                                                    <SelectItem value="admin">مدیر (Admin)</SelectItem>
                                                    <SelectItem value="user">کاربر (User)</SelectItem>
                                                    <SelectItem value="viewer">بیننده (Viewer)</SelectItem>
                                                </>
                                            )}
                                        </SelectContent>
                                    </Select>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <div className="grid grid-cols-2 gap-4">
                            <FormField
                                control={form.control}
                                name="daily_request_limit"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>محدودیت روزانه</FormLabel>
                                        <FormControl>
                                            <Input
                                                type="number"
                                                {...field}
                                                onChange={(e) =>
                                                    field.onChange(parseInt(e.target.value))
                                                }
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="monthly_request_limit"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>محدودیت ماهانه</FormLabel>
                                        <FormControl>
                                            <Input
                                                type="number"
                                                {...field}
                                                onChange={(e) =>
                                                    field.onChange(parseInt(e.target.value))
                                                }
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>

                        <FormField
                            control={form.control}
                            name="is_active"
                            render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                    <div className="space-y-0.5">
                                        <FormLabel className="text-base">وضعیت کاربر</FormLabel>
                                        <FormDescription>
                                            کاربر فعال می‌تواند وارد سیستم شود
                                        </FormDescription>
                                    </div>
                                    <FormControl>
                                        <Switch
                                            checked={field.value}
                                            onCheckedChange={field.onChange}
                                        />
                                    </FormControl>
                                </FormItem>
                            )}
                        />

                        <DialogFooter>
                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => onOpenChange(false)}
                                disabled={isLoading}
                            >
                                انصراف
                            </Button>
                            <Button type="submit" disabled={isLoading}>
                                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                ذخیره تغییرات
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
