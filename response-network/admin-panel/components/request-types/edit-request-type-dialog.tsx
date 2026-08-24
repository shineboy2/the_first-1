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
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
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
import { Textarea } from "@/components/ui/textarea";
import { requestService } from "@/lib/services/admin-api";
import type { RequestType } from "@/lib/services/admin-api";
import { Alert, AlertDescription } from "@/components/ui/alert";

const formSchema = z.object({
    name: z.string().min(3, "نام باید حداقل ۳ کاراکتر باشد"),
    description: z.string().optional(),
    is_active: z.boolean(),
    version: z.string().min(1, "نسخه الزامی است"),
    max_items_per_request: z.coerce.number().min(1, "حداقل 1").max(10000, "حداکثر 10000"),
    execution_method: z.string().default("elasticsearch"),
    external_api_id: z.string().optional().nullable(),
    object_storage_config_id: z.string().optional().nullable(),
});

type EditRequestTypeFormData = z.infer<typeof formSchema>;

interface EditRequestTypeDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
    requestType: RequestType | null;
}

export function EditRequestTypeDialog({
    open,
    onOpenChange,
    onSuccess,
    requestType,
}: EditRequestTypeDialogProps) {
    const [error, setError] = useState<string | null>(null);
    const [externalApis, setExternalApis] = useState<any[]>([]);
    const [loadingApis, setLoadingApis] = useState(false);
    
    // Add state for object storage configs
    const [objectStorageConfigs, setObjectStorageConfigs] = useState<any[]>([]);
    const [loadingStorage, setLoadingStorage] = useState(false);

    useEffect(() => {
        const fetchExternalApis = async () => {
            try {
                setLoadingApis(true);
                const { externalApiService } = await import('@/lib/services/admin-api');
                const apis = await externalApiService.getExternalAPIs();
                setExternalApis(apis);
            } catch (err) {
                console.error("Error fetching external apis:", err);
            } finally {
                setLoadingApis(false);
            }
        };
        const fetchObjectStorageConfigs = async () => {
            try {
                setLoadingStorage(true);
                const { adminApi } = await import('@/lib/services/admin-api');
                const configs = await adminApi.objectStorageConfigService.getConfigs();
                setObjectStorageConfigs(Array.isArray(configs) ? configs : []);
            } catch (err) {
                console.error("Error fetching object storage configs:", err);
            } finally {
                setLoadingStorage(false);
            }
        };
        fetchExternalApis();
        fetchObjectStorageConfigs();
    }, []);

    const form = useForm<EditRequestTypeFormData>({
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        resolver: zodResolver(formSchema) as any,
        defaultValues: {
            name: requestType?.name || "",
            description: requestType?.description || "",
            is_active: requestType?.is_active ?? true,
            version: requestType?.version || "1.0.0",
            max_items_per_request: requestType?.max_items_per_request || 100,
            // @ts-ignore
            execution_method: requestType?.execution_method || "elasticsearch",
            // @ts-ignore
            external_api_id: requestType?.external_api_id || null,
            // @ts-ignore
            object_storage_config_id: requestType?.object_storage_config_id || null,
        },
    });

    const executionMethod = form.watch("execution_method");

    useEffect(() => {
        if (open && requestType) {
            form.reset({
                name: requestType.name,
                description: requestType.description || "",
                is_active: requestType.is_active,
                version: requestType.version || "1.0.0",
                max_items_per_request: requestType.max_items_per_request || 100,
                // @ts-ignore
                execution_method: requestType.execution_method || "elasticsearch",
                // @ts-ignore
                external_api_id: requestType.external_api_id || null,
                // @ts-ignore
                object_storage_config_id: requestType.object_storage_config_id || null,
            });
        } else if (!open) {
            form.reset({
                name: "",
                description: "",
                is_active: true,
                version: "1.0.0",
                max_items_per_request: 100,
                execution_method: "elasticsearch",
                external_api_id: null,
                object_storage_config_id: null,
            });
            setError(null);
        }
    }, [requestType, form, open]);

    const onSubmit = async (data: EditRequestTypeFormData) => {
        if (!requestType) return;

        try {
            setError(null);
            await requestService.updateRequestType(requestType.id, data);
            onSuccess();
            onOpenChange(false);
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (err: any) {
            console.error("Error updating request type:", err);
            setError(
                err.response?.data?.detail || "خطا در ویرایش نوع درخواست. لطفاً مجدداً تلاش کنید."
            );
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle>ویرایش نوع درخواست</DialogTitle>
                    <DialogDescription>
                        ویرایش اطلاعات نوع درخواست {requestType?.name}
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
                                    <FormLabel>نام</FormLabel>
                                    <FormControl>
                                        <Input {...field} className="text-left" dir="ltr" />
                                    </FormControl>
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
                                        <Textarea {...field} rows={3} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="execution_method"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>روش اجرا</FormLabel>
                                    <Select
                                        onValueChange={field.onChange}
                                        defaultValue={field.value}
                                    >
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="انتخاب روش اجرا" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            <SelectItem value="elasticsearch">Elasticsearch</SelectItem>
                                            <SelectItem value="external_api">API خارجی</SelectItem>
                                            <SelectItem value="file_request">درخواست فایلی (FTP)</SelectItem>
                                            <SelectItem value="object_storage">آبجکت استورج (Ceph/MinIO)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        {executionMethod === "external_api" && (
                            <FormField
                                control={form.control}
                                name="external_api_id"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>API خارجی</FormLabel>
                                        <Select
                                            onValueChange={field.onChange}
                                            defaultValue={field.value || undefined}
                                        >
                                            <FormControl>
                                                <SelectTrigger>
                                                    <SelectValue placeholder={loadingApis ? "در حال دریافت..." : "انتخاب API خارجی"} />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                {externalApis && externalApis.length > 0 ? (
                                                    externalApis.map(api => (
                                                        <SelectItem key={api.id} value={api.id}>{api.name}</SelectItem>
                                                    ))
                                                ) : (
                                                    <SelectItem value="none" disabled>
                                                        {loadingApis ? "در حال دریافت..." : "هیچ API خارجی یافت نشد"}
                                                    </SelectItem>
                                                )}
                                            </SelectContent>
                                        </Select>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        )}

                        <div className="grid grid-cols-2 gap-4">
                            <FormField
                                control={form.control}
                                name="version"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>نسخه</FormLabel>
                                        <FormControl>
                                            <Input {...field} className="text-left" dir="ltr" />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="max_items_per_request"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>حداکثر آیتم در هر درخواست</FormLabel>
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
                                            آیا این نوع درخواست قابل استفاده است؟
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

                        {executionMethod === "object_storage" && (
                            <FormField
                                control={form.control}
                                name="object_storage_config_id"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>انتخاب تنظیمات Object Storage</FormLabel>
                                        <Select
                                            onValueChange={field.onChange}
                                            value={field.value || ""}
                                        >
                                            <FormControl>
                                                <SelectTrigger disabled={loadingStorage}>
                                                    <SelectValue placeholder={loadingStorage ? "در حال بارگذاری..." : "انتخاب تنظیمات..."} />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                {objectStorageConfigs.map((config) => (
                                                    <SelectItem key={config.id} value={config.id}>
                                                        {config.display_name || config.name}
                                                    </SelectItem>
                                                ))}
                                                {objectStorageConfigs.length === 0 && !loadingStorage && (
                                                    <SelectItem value="none" disabled>
                                                        هیچ تنظیمی یافت نشد
                                                    </SelectItem>
                                                )}
                                            </SelectContent>
                                        </Select>
                                        <FormDescription>
                                            سرور Ceph یا MinIO که فایل‌ها از آن دانلود می‌شوند را انتخاب کنید
                                        </FormDescription>
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
