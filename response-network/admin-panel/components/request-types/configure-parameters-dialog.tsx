"use client";

import { useEffect, useState } from "react";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2, Plus, Trash2 } from "lucide-react";

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
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { requestService, externalApiService } from "@/lib/services/admin-api";
import type { RequestType, ExternalAPI } from "@/lib/services/admin-api";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Textarea } from "@/components/ui/textarea";
import {
    FormDescription,
} from "@/components/ui/form";

const parameterSchema = z.object({
    name: z.string().min(1, "نام الزامی است"),
    description: z.string().optional(),
    parameter_type: z.string().min(1, "نوع الزامی است"),
    is_required: z.boolean(),
    validation_rules: z.union([z.record(z.any()), z.null()]).optional().transform(val => val === undefined || val === null || (typeof val === 'object' && Object.keys(val).length === 0) ? null : val),
    placeholder_key: z.string().min(1, "کلید placeholder الزامی است"),
});

const fieldMappingEntrySchema = z.object({
    key: z.string().min(1, "نام فیلد الستیک الزامی است"),
    value: z.string().min(1, "نام نمایشی الزامی است"),
});

const indexMappingEntrySchema = z.object({
    key: z.string().min(1, "نام ایندکس الزامی است"),
    value: z.string().min(1, "نام نمایشی الزامی است"),
});

const formSchema = z.object({
    parameters: z.array(parameterSchema),
    max_items_per_request: z.coerce.number().min(1).max(10000),
    execution_method: z.string().default("elasticsearch"),
    external_api_id: z.string().optional().nullable(),
    target_index: z.string().min(1, "نام ایندکس الزامی است").default("default"),
    field_mapping_entries: z.array(fieldMappingEntrySchema),
    index_mapping_entries: z.array(indexMappingEntrySchema),
    object_storage_mapping_str: z.string().optional(),
});

type ConfigureParametersFormData = z.infer<typeof formSchema>;

interface ConfigureParametersDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
    requestType: RequestType | null;
}

export function ConfigureParametersDialog({
    open,
    onOpenChange,
    onSuccess,
    requestType,
}: ConfigureParametersDialogProps) {
    const [error, setError] = useState<string | null>(null);
    const [externalApis, setExternalApis] = useState<ExternalAPI[]>([]);
    const [loadingApis, setLoadingApis] = useState(false);

    const form = useForm<ConfigureParametersFormData>({
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        resolver: zodResolver(formSchema) as any,
        defaultValues: {
            parameters: [],
            max_items_per_request: 100,
            field_mapping_entries: [],
            index_mapping_entries: [],
            // @ts-ignore - execution_method exists on backend response but typescript might complain if RequestType interface is missing it
            execution_method: requestType?.execution_method || "elasticsearch",
            // @ts-ignore
            external_api_id: requestType?.external_api_id || null,
            target_index: requestType?.available_indices?.join(", ") || "default",
            object_storage_mapping_str: "{}",
        },
    });

    const executionMethod = form.watch("execution_method");

    useEffect(() => {
        if (open) {
            fetchExternalApis();
        }
    }, [open]);

    const fetchExternalApis = async () => {
        try {
            setLoadingApis(true);
            const apis = await externalApiService.getExternalAPIs();
            setExternalApis(apis);
        } catch (err) {
            console.error("Error fetching external apis:", err);
        } finally {
            setLoadingApis(false);
        }
    };

    const { fields, append, remove } = useFieldArray({
        control: form.control,
        name: "parameters",
    });

    const { fields: fieldMapFields, append: appendFieldMap, remove: removeFieldMap } = useFieldArray({
        control: form.control,
        name: "field_mapping_entries",
    });

    const { fields: indexMapFields, append: appendIndexMap, remove: removeIndexMap } = useFieldArray({
        control: form.control,
        name: "index_mapping_entries",
    });

    useEffect(() => {
        if (open && requestType) {
            // Convert mapping objects to entry arrays for the form
            const fieldMappingObj = requestType.field_mapping || {};
            const indexMappingObj = requestType.index_mapping || {};
            const fieldEntries = Object.entries(fieldMappingObj).map(([key, value]) => ({ key, value: value as string }));
            const indexEntries = Object.entries(indexMappingObj).map(([key, value]) => ({ key, value: value as string }));

            form.reset({
                parameters: requestType.parameters || [],
                max_items_per_request: requestType.max_items_per_request || 100,
                // @ts-ignore
                execution_method: requestType.execution_method || "elasticsearch",
                // @ts-ignore
                external_api_id: requestType.external_api_id || null,
                target_index: requestType.available_indices?.join(", ") || "default",
                field_mapping_entries: fieldEntries,
                index_mapping_entries: indexEntries,
                // @ts-ignore
                object_storage_mapping_str: requestType.object_storage_mapping
                    // @ts-ignore
                    ? JSON.stringify(requestType.object_storage_mapping, null, 2)
                    : '{\n  "file_paths": ["doc.path"],\n  "bucket_field": "doc.bucket",\n  "base_prefix": ""\n}',
            });
        } else if (!open) {
            form.reset({
                parameters: [],
                max_items_per_request: 100,
                execution_method: "elasticsearch",
                external_api_id: null,
                target_index: "default",
                field_mapping_entries: [],
                index_mapping_entries: [],
                object_storage_mapping_str: '{\n  "file_paths": ["doc.path"],\n  "bucket_field": "doc.bucket",\n  "base_prefix": ""\n}',
            });
            setError(null);
        }
    }, [requestType, form, open]);

    const onSubmit = async (data: ConfigureParametersFormData) => {
        if (!requestType) return;

        try {
            setError(null);

            // Map target_index to available_indices array (support comma-separated multiple indices)
            const indices = data.target_index.split(",").map(i => i.trim()).filter(i => i);

            // Convert entry arrays back to mapping objects
            const fieldMapping: Record<string, string> = {};
            for (const entry of data.field_mapping_entries || []) {
                if (entry.key && entry.value) fieldMapping[entry.key] = entry.value;
            }
            const indexMapping: Record<string, string> = {};
            for (const entry of data.index_mapping_entries || []) {
                if (entry.key && entry.value) indexMapping[entry.key] = entry.value;
            }
            let objectStorageMappingObj = null;
            if (data.execution_method === "object_storage" && data.object_storage_mapping_str) {
                try {
                    objectStorageMappingObj = JSON.parse(data.object_storage_mapping_str);
                } catch (e) {
                    setError("فرمت JSON برای تنظیمات آبجکت استورج نامعتبر است");
                    return;
                }
            }

            const submitData = {
                ...data,
                available_indices: indices.length > 0 ? indices : ["default"],
                field_mapping: fieldMapping,
                index_mapping: indexMapping,
                object_storage_mapping: objectStorageMappingObj,
                // Preserve current is_active and is_public values from the existing requestType
                // These are managed separately (e.g. activate/deactivate buttons), not in this form
                is_active: requestType.is_active ?? false,
                is_public: requestType.is_public ?? false,
            };

            await requestService.configureRequestTypeParams(requestType.id, submitData);
            onSuccess();
            onOpenChange(false);
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (err: any) {
            console.error("Error configuring parameters:", err);
            setError(
                err.response?.data?.detail || "خطا در تنظیم پارامترها. لطفاً مجدداً تلاش کنید."
            );
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>تنظیم پارامترها</DialogTitle>
                    <DialogDescription>
                        تنظیم پارامترهای نوع درخواست {requestType?.name}
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

                        <div className="grid grid-cols-2 gap-4">
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
                                                <SelectItem value="elasticsearch">پایگاه داده (Elasticsearch)</SelectItem>
                                                <SelectItem value="external_api">API خارجی (External API)</SelectItem>
                                                <SelectItem value="file_request">درخواست فایلی (File Request)</SelectItem>
                                                <SelectItem value="object_storage">آبجکت استورج (Object Storage)</SelectItem>
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

                            {executionMethod === "elasticsearch" && (
                                <FormField
                                    control={form.control}
                                    name="target_index"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>نام ایندکس‌ها (با کاما جدا کنید)</FormLabel>
                                            <FormControl>
                                                <Input className="text-left" dir="ltr" placeholder="مثال: index-1, index-2" {...field} />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            )}
                        </div>

                        {executionMethod === "object_storage" && (
                            <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
                                <div>
                                    <h4 className="font-medium text-sm">تنظیمات نگاشت Object Storage</h4>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        مشخص کنید کدام فیلد از خروجی Elasticsearch شامل مسیر فایل است.
                                        باکت پیش‌فرض از تنظیمات Object Storage خوانده می‌شود.
                                    </p>
                                </div>
                                <FormField
                                    control={form.control}
                                    name="object_storage_mapping_str"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>مسیر فیلد مسیر فایل (dot notation)</FormLabel>
                                            <FormControl>
                                                <Input
                                                    className="font-mono text-sm text-left"
                                                    dir="ltr"
                                                    placeholder="مثال: _source.image_path یا doc.photo"
                                                    value={(() => {
                                                        try {
                                                            const parsed = JSON.parse(field.value || '{}');
                                                            return (parsed.file_paths || [''])[0] || '';
                                                        } catch { return ''; }
                                                    })()}
                                                    onChange={(e) => {
                                                        try {
                                                            const current = JSON.parse(field.value || '{}');
                                                            current.file_paths = e.target.value ? [e.target.value] : [];
                                                            field.onChange(JSON.stringify(current, null, 2));
                                                        } catch {
                                                            field.onChange(JSON.stringify({ file_paths: [e.target.value], bucket: '', base_prefix: '' }, null, 2));
                                                        }
                                                    }}
                                                />
                                            </FormControl>
                                            <FormDescription>
                                                نام فیلد در نتیجه ES که شامل آدرس فایل/عکس است.
                                            </FormDescription>

                                            <div className="mt-3">
                                                <FormLabel>باکت اختصاصی (اختیاری)</FormLabel>
                                                <Input
                                                    className="font-mono text-sm text-left mt-1"
                                                    dir="ltr"
                                                    placeholder="خالی = از باکت پیش‌فرض تنظیمات Object Storage استفاده می‌شود"
                                                    value={(() => {
                                                        try {
                                                            const parsed = JSON.parse(field.value || '{}');
                                                            return parsed.bucket || '';
                                                        } catch { return ''; }
                                                    })()}
                                                    onChange={(e) => {
                                                        try {
                                                            const current = JSON.parse(field.value || '{}');
                                                            current.bucket = e.target.value;
                                                            field.onChange(JSON.stringify(current, null, 2));
                                                        } catch {
                                                            field.onChange(JSON.stringify({ file_paths: [], bucket: e.target.value, base_prefix: '' }, null, 2));
                                                        }
                                                    }}
                                                />
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    اگر فایل‌ها در باکت متفاوتی هستند، نام آن باکت را اینجا وارد کنید.
                                                </p>
                                            </div>

                                            <details className="mt-3">
                                                <summary className="text-xs text-muted-foreground cursor-pointer">مشاهده JSON خام</summary>
                                                <Textarea
                                                    value={field.value || ''}
                                                    onChange={field.onChange}
                                                    rows={4}
                                                    className="font-mono text-xs mt-1"
                                                    dir="ltr"
                                                />
                                            </details>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>
                        )}

                        <div className="space-y-4 pt-4 border-t">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-medium">پارامترها</h3>
                                <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    onClick={() =>
                                        append({
                                            name: "",
                                            description: "",
                                            parameter_type: "string",
                                            is_required: false,
                                            validation_rules: null,
                                            placeholder_key: "",
                                        })
                                    }
                                >
                                    <Plus className="h-4 w-4 mr-2" />
                                    افزودن پارامتر
                                </Button>
                            </div>

                            {fields.length === 0 && (
                                <p className="text-sm text-muted-foreground text-center py-4">
                                    هیچ پارامتری تعریف نشده است. برای افزودن پارامتر کلیک کنید.
                                </p>
                            )}

                            {fields.map((field, index) => (
                                <div key={field.id} className="border rounded-lg p-4 space-y-3">
                                    <div className="flex items-center justify-between">
                                        <h4 className="font-medium">پارامتر {index + 1}</h4>
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => remove(index)}
                                        >
                                            <Trash2 className="h-4 w-4 text-red-600" />
                                        </Button>
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        <FormField
                                            control={form.control}
                                            name={`parameters.${index}.name`}
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
                                            name={`parameters.${index}.parameter_type`}
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>نوع</FormLabel>
                                                    <Select
                                                        onValueChange={field.onChange}
                                                        defaultValue={field.value}
                                                    >
                                                        <FormControl>
                                                            <SelectTrigger>
                                                                <SelectValue />
                                                            </SelectTrigger>
                                                        </FormControl>
                                                        <SelectContent>
                                                            <SelectItem value="string">String</SelectItem>
                                                            <SelectItem value="number">Number</SelectItem>
                                                            <SelectItem value="boolean">Boolean</SelectItem>
                                                            <SelectItem value="array">Array</SelectItem>
                                                            <SelectItem value="object">Object</SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                    </div>

                                    <FormField
                                        control={form.control}
                                        name={`parameters.${index}.description`}
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

                                    <FormField
                                        control={form.control}
                                        name={`parameters.${index}.placeholder_key`}
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>کلید Placeholder (برای استفاده در Query)</FormLabel>
                                                <FormControl>
                                                    <Input {...field} className="text-left" dir="ltr" placeholder="keyword" />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />

                                    <FormField
                                        control={form.control}
                                        name={`parameters.${index}.is_required`}
                                        render={({ field }) => (
                                            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
                                                <FormLabel className="text-sm">الزامی</FormLabel>
                                                <FormControl>
                                                    <Switch
                                                        checked={field.value}
                                                        onCheckedChange={field.onChange}
                                                    />
                                                </FormControl>
                                            </FormItem>
                                        )}
                                    />
                                </div>
                            ))}
                        </div>

                        {/* Index Mapping Section */}
                        {executionMethod === "elasticsearch" && (
                            <div className="space-y-4 border-t pt-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-lg font-medium">نگاشت ایندکس‌ها</h3>
                                        <p className="text-sm text-muted-foreground">نام واقعی ایندکس الستیک‌سرچ را به نام نمایشی دلخواه تبدیل کنید.</p>
                                    </div>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={() => appendIndexMap({ key: "", value: "" })}
                                    >
                                        <Plus className="h-4 w-4 mr-2" />
                                        افزودن
                                    </Button>
                                </div>

                                {indexMapFields.length === 0 && (
                                    <p className="text-sm text-muted-foreground text-center py-2">
                                        نگاشتی تعریف نشده. نام واقعی ایندکس‌ها نمایش داده خواهد شد.
                                    </p>
                                )}

                                {indexMapFields.map((field, index) => (
                                    <div key={field.id} className="flex items-center gap-2">
                                        <FormField
                                            control={form.control}
                                            name={`index_mapping_entries.${index}.key`}
                                            render={({ field }) => (
                                                <FormItem className="flex-1">
                                                    <FormControl>
                                                        <Input {...field} className="text-left" dir="ltr" placeholder="نام واقعی ایندکس (مثلاً hotels_idx)" />
                                                    </FormControl>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                        <span className="text-muted-foreground">←</span>
                                        <FormField
                                            control={form.control}
                                            name={`index_mapping_entries.${index}.value`}
                                            render={({ field }) => (
                                                <FormItem className="flex-1">
                                                    <FormControl>
                                                        <Input {...field} placeholder="نام نمایشی (مثلاً اطلاعات هتل‌ها)" />
                                                    </FormControl>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                        <Button type="button" variant="ghost" size="sm" onClick={() => removeIndexMap(index)}>
                                            <Trash2 className="h-4 w-4 text-red-600" />
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Field Mapping Section */}
                        {executionMethod === "elasticsearch" && (
                            <div className="space-y-4 border-t pt-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-lg font-medium">نگاشت فیلدها</h3>
                                        <p className="text-sm text-muted-foreground">نام فیلدهای خروجی الستیک‌سرچ را به نام فارسی دلخواه تبدیل کنید.</p>
                                    </div>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={() => appendFieldMap({ key: "", value: "" })}
                                    >
                                        <Plus className="h-4 w-4 mr-2" />
                                        افزودن
                                    </Button>
                                </div>

                                {fieldMapFields.length === 0 && (
                                    <p className="text-sm text-muted-foreground text-center py-2">
                                        نگاشتی تعریف نشده. نام اصلی فیلدها نمایش داده خواهد شد.
                                    </p>
                                )}

                                {fieldMapFields.map((field, index) => (
                                    <div key={field.id} className="flex items-center gap-2">
                                        <FormField
                                            control={form.control}
                                            name={`field_mapping_entries.${index}.key`}
                                            render={({ field }) => (
                                                <FormItem className="flex-1">
                                                    <FormControl>
                                                        <Input {...field} className="text-left" dir="ltr" placeholder="نام فیلد الستیک (مثلاً name)" />
                                                    </FormControl>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                        <span className="text-muted-foreground">←</span>
                                        <FormField
                                            control={form.control}
                                            name={`field_mapping_entries.${index}.value`}
                                            render={({ field }) => (
                                                <FormItem className="flex-1">
                                                    <FormControl>
                                                        <Input {...field} placeholder="نام نمایشی (مثلاً نام)" />
                                                    </FormControl>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                        <Button type="button" variant="ghost" size="sm" onClick={() => removeFieldMap(index)}>
                                            <Trash2 className="h-4 w-4 text-red-600" />
                                        </Button>
                                    </div>
                                ))}
                            </div>
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
                                ذخیره تنظیمات
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
