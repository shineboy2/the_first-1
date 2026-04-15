"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
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
import { Switch } from "@/components/ui/switch";
import { profileTypeService } from "@/lib/services/admin-api";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";
import adminApi, { ExternalAPI, ProfileType } from "@/lib/services/admin-api";

const formSchema = z.object({
    name: z
        .string()
        .min(3, "نام باید حداقل ۳ کاراکتر باشد")
        .regex(/^[a-zA-Z0-9_-]+$/, "نام فقط می‌تواند شامل حروف انگلیسی، اعداد و خط تیره باشد"),
    description: z.string().optional(),
    daily_request_limit: z.coerce.number().min(0, "محدودیت نمی‌تواند منفی باشد"),
    monthly_request_limit: z.coerce.number().min(0, "محدودیت نمی‌تواند منفی باشد"),
    is_active: z.boolean(),
    permissions: z.object({
        allowed_external_apis: z.array(z.string()).default([]),
    }).default({ allowed_external_apis: [] }),
});

type EditProfileTypeFormData = z.infer<typeof formSchema>;

interface EditProfileTypeDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
    profileType: ProfileType | null;
}

export function EditProfileTypeDialog({
    open,
    onOpenChange,
    onSuccess,
    profileType,
}: EditProfileTypeDialogProps) {
    const [error, setError] = useState<string | null>(null);
    const [externalApis, setExternalApis] = useState<ExternalAPI[]>([]);

    import("react").then((React) => {
        React.useEffect(() => {
            if (open) {
                adminApi.externalApiService.getExternalAPIs().then(setExternalApis).catch(console.error);
            }
        }, [open]);
    });

    const form = useForm<EditProfileTypeFormData>({
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        resolver: zodResolver(formSchema) as any,
        defaultValues: {
            name: profileType?.name || "",
            description: profileType?.description || "",
            daily_request_limit: profileType?.daily_request_limit || 0,
            monthly_request_limit: profileType?.monthly_request_limit || 0,
            is_active: profileType?.is_active ?? true,
            permissions: {
                allowed_external_apis: profileType?.permissions?.allowed_external_apis || [],
            }
        },
    });

    useEffect(() => {
        // Reset form values when profileType changes and the dialog is open
        // This ensures that if the dialog is opened for a different profileType,
        // the form fields are updated correctly.
        if (open && profileType) {
            form.reset({
                name: profileType.name,
                description: profileType.description || "",
                daily_request_limit: profileType.daily_request_limit,
                monthly_request_limit: profileType.monthly_request_limit,
                is_active: profileType.is_active,
                permissions: {
                    allowed_external_apis: profileType.permissions?.allowed_external_apis || [],
                }
            });
        } else if (!open) {
            // When the dialog closes, reset the form to its initial empty state
            // or the default values defined in useForm for the next open.
            form.reset({
                name: "",
                description: "",
                daily_request_limit: 0,
                monthly_request_limit: 0,
                is_active: true,
                permissions: { allowed_external_apis: [] }
            });
            setError(null); // Clear any previous errors
        }
    }, [profileType, form, open]);

    const onSubmit = async (data: EditProfileTypeFormData) => {
        if (!profileType) return;

        try {
            setError(null);
            // If it's a built-in type, we can't change the name, so we use the original name
            // Actually the API endpoint uses the original name in the URL to identify the resource
            await profileTypeService.updateProfileType(profileType.name, data);
            onSuccess();
            onOpenChange(false);
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (err: any) {
            console.error("Error updating profile type:", err);
            setError(
                err.response?.data?.detail || "خطا در ویرایش نوع پروفایل. لطفاً مجدداً تلاش کنید."
            );
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>ویرایش نوع پروفایل</DialogTitle>
                    <DialogDescription>
                        ویرایش اطلاعات پروفایل {profileType?.name}
                    </DialogDescription>
                </DialogHeader>

                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                        {error && (
                            <Alert variant="destructive">
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}

                        <FormField
                            control={form.control}
                            name="name"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>نام (شناسه)</FormLabel>
                                    <FormControl>
                                        <Input
                                            {...field}
                                            className="text-left"
                                            dir="ltr"
                                            disabled={profileType?.is_builtin} // Disable name editing for built-in types
                                        />
                                    </FormControl>
                                    {profileType?.is_builtin && (
                                        <FormDescription>
                                            نام پروفایل‌های سیستمی قابل تغییر نیست.
                                        </FormDescription>
                                    )}
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="description"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>توضیحات</FormLabel>
                                    <FormControl>
                                        <Input {...field} />
                                    </FormControl>
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
                                            <Input type="number" {...field} />
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
                                            <Input type="number" {...field} />
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
                                        <FormLabel className="text-base">وضعیت فعال</FormLabel>
                                        <FormDescription>
                                            آیا این نوع پروفایل قابل استفاده است؟
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

                        {externalApis.length > 0 && (
                            <FormField
                                control={form.control}
                                name="permissions.allowed_external_apis"
                                render={() => (
                                    <FormItem>
                                        <div className="mb-4">
                                            <FormLabel className="text-base">دسترسی API های خارجی</FormLabel>
                                            <FormDescription>
                                                کدام API های خارجی برای این نوع پروفایل مجاز است؟
                                            </FormDescription>
                                        </div>
                                        {externalApis.map((api) => (
                                            <FormField
                                                key={api.id}
                                                control={form.control}
                                                name="permissions.allowed_external_apis"
                                                render={({ field }) => {
                                                    return (
                                                        <FormItem
                                                            key={api.id}
                                                            className="flex flex-row items-start space-x-3 space-x-reverse space-y-0 rounded-md border p-4"
                                                        >
                                                            <FormControl>
                                                                <Checkbox
                                                                    disabled={profileType?.name === "admin" && api.is_active} // Optional: logic to not allow removing from admin
                                                                    checked={field.value?.includes(api.name)}
                                                                    onCheckedChange={(checked) => {
                                                                        return checked
                                                                            ? field.onChange([...(field.value || []), api.name])
                                                                            : field.onChange(
                                                                                field.value?.filter(
                                                                                    (value) => value !== api.name
                                                                                )
                                                                            )
                                                                    }}
                                                                />
                                                            </FormControl>
                                                            <div className="space-y-1 leading-none">
                                                                <FormLabel className="font-mono text-sm">
                                                                    {api.name}
                                                                </FormLabel>
                                                            </div>
                                                        </FormItem>
                                                    )
                                                }}
                                            />
                                        ))}
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        )}

                        <DialogFooter>
                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => onOpenChange(false)}
                            >
                                انصراف
                            </Button>
                            <Button type="submit" disabled={form.formState.isSubmitting}>
                                {form.formState.isSubmitting && (
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                )}
                                ذخیره تغییرات
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
