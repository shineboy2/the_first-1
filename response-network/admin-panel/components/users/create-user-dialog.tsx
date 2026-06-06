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
import type { ProfileType } from "@/lib/services/admin-api";

const createUserSchema = z.object({
    username: z.string().min(3, "نام کاربری باید حداقل 3 کاراکتر باشد"),
    email: z.string().email("ایمیل معتبر وارد کنید"),
    password: z.string().min(8, "رمز عبور باید حداقل 8 کاراکتر باشد"),
    full_name: z.string().min(1, "نام کامل الزامی است"),
    profile_type: z.string().min(1, "نوع پروفایل الزامی است"),
    daily_request_limit: z.number().min(1).default(1000),
    monthly_request_limit: z.number().min(1).default(10000),
    force_password_change: z.boolean().default(false),
    allowed_ips_str: z.string().optional(),
});

type CreateUserFormData = z.infer<typeof createUserSchema>;

interface CreateUserDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

export function CreateUserDialog({
    open,
    onOpenChange,
    onSuccess,
}: CreateUserDialogProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [profileTypes, setProfileTypes] = useState<ProfileType[]>([]);
    const [loadingProfileTypes, setLoadingProfileTypes] = useState(true);

    const form = useForm<CreateUserFormData>({
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        resolver: zodResolver(createUserSchema) as any,
        defaultValues: {
            username: "",
            email: "",
            password: "",
            full_name: "",
            profile_type: "user",
            daily_request_limit: 1000,
            monthly_request_limit: 10000,
            force_password_change: true,
            allowed_ips_str: "",
        },
    });

    // Fetch profile types on mount
    useEffect(() => {
        const fetchProfileTypes = async () => {
            try {
                setLoadingProfileTypes(true);
                const types = await profileTypeService.getProfileTypes();
                setProfileTypes(types.filter(pt => pt.is_active));
            } catch (error) {
                console.error("Error fetching profile types:", error);
            } finally {
                setLoadingProfileTypes(false);
            }
        };
        fetchProfileTypes();
    }, []);

    const onSubmit = async (data: CreateUserFormData) => {
        try {
            setIsLoading(true);
            const submitData = {
                ...data,
                allowed_ips: data.allowed_ips_str ? data.allowed_ips_str.split(",").map(ip => ip.trim()).filter(Boolean) : []
            };
            // @ts-ignore
            delete submitData.allowed_ips_str;

            await userService.createUser(submitData);
            form.reset();
            onSuccess();
            onOpenChange(false);
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (error: any) {
            console.error("Error creating user:", error);
            form.setError("root", {
                message: error.response?.data?.detail || "خطا در ایجاد کاربر",
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>ایجاد کاربر جدید</DialogTitle>
                    <DialogDescription>
                        اطلاعات کاربر جدید را وارد کنید
                    </DialogDescription>
                </DialogHeader>

                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                        {form.formState.errors.root && (
                            <div className="text-sm text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded">
                                {form.formState.errors.root.message}
                            </div>
                        )}

                        <div className="grid grid-cols-2 gap-4">
                            <FormField
                                control={form.control}
                                name="username"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>نام کاربری</FormLabel>
                                        <FormControl>
                                            <Input placeholder="username" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="email"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>ایمیل</FormLabel>
                                        <FormControl>
                                            <Input
                                                type="email"
                                                placeholder="user@example.com"
                                                {...field}
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>

                        <FormField
                            control={form.control}
                            name="full_name"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>نام کامل</FormLabel>
                                    <FormControl>
                                        <Input placeholder="نام و نام خانوادگی" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="password"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>رمز عبور</FormLabel>
                                    <FormControl>
                                        <Input
                                            type="password"
                                            placeholder="حداقل 8 کاراکتر"
                                            {...field}
                                        />
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
                                        defaultValue={field.value}
                                    >
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="انتخاب نوع کاربر" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            {loadingProfileTypes ? (
                                                <div className="flex items-center justify-center p-2">
                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                </div>
                                            ) : profileTypes.length > 0 ? (
                                                profileTypes.map((pt) => (
                                                    <SelectItem key={pt.name} value={pt.name}>
                                                        {pt.name}
                                                    </SelectItem>
                                                ))
                                            ) : (
                                                <div className="p-2 text-sm text-muted-foreground">
                                                    هیچ نوع پروفایلی یافت نشد
                                                </div>
                                            )}
                                        </SelectContent>
                                    </Select>
                                    <FormDescription>
                                        سطح دسترسی کاربر را مشخص کنید
                                    </FormDescription>
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
                                        <FormDescription>تعداد درخواست در روز</FormDescription>
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
                                        <FormDescription>تعداد درخواست در ماه</FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>

                        <FormField
                            control={form.control}
                            name="force_password_change"
                            render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4 border-amber-200 dark:border-amber-900 bg-amber-50/50 dark:bg-amber-900/10">
                                    <div className="space-y-0.5">
                                        <FormLabel className="text-base">اجبار به تغییر رمز عبور</FormLabel>
                                        <FormDescription>
                                            کاربر در اولین ورود مجبور به تغییر رمز خواهد شد
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

                        <FormField
                            control={form.control}
                            name="allowed_ips_str"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>آدرس‌های IP مجاز (با کاما جدا کنید)</FormLabel>
                                    <FormControl>
                                        <Input placeholder="192.168.1.1, 10.0.0.1" {...field} />
                                    </FormControl>
                                    <FormDescription>
                                        خالی گذاشتن به معنی دسترسی از همه IPها است.
                                    </FormDescription>
                                    <FormMessage />
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
                                ایجاد کاربر
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
