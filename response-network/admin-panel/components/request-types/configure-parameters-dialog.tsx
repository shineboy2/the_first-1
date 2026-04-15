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
import { requestService } from "@/lib/services/admin-api";
import type { RequestType } from "@/lib/services/admin-api";
import { Alert, AlertDescription } from "@/components/ui/alert";

const parameterSchema = z.object({
    name: z.string().min(1, "نام الزامی است"),
    description: z.string().optional(),
    parameter_type: z.string().min(1, "نوع الزامی است"),
    is_required: z.boolean(),
    validation_rules: z.union([z.record(z.any()), z.null()]).optional().transform(val => val === undefined || val === null || (typeof val === 'object' && Object.keys(val).length === 0) ? null : val),
    placeholder_key: z.string().min(1, "کلید placeholder الزامی است"),
});

const formSchema = z.object({
    parameters: z.array(parameterSchema),
    max_items_per_request: z.coerce.number().min(1).max(10000),
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

    const form = useForm<ConfigureParametersFormData>({
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        resolver: zodResolver(formSchema) as any,
        defaultValues: {
            parameters: [],
            max_items_per_request: 100,
        },
    });

    const { fields, append, remove } = useFieldArray({
        control: form.control,
        name: "parameters",
    });

    useEffect(() => {
        if (open && requestType) {
            form.reset({
                parameters: requestType.parameters || [],
                max_items_per_request: requestType.max_items_per_request || 100,
            });
        } else if (!open) {
            form.reset({
                parameters: [],
                max_items_per_request: 100,
            });
            setError(null);
        }
    }, [requestType, form, open]);

    const onSubmit = async (data: ConfigureParametersFormData) => {
        if (!requestType) return;

        try {
            setError(null);
            await requestService.configureRequestTypeParams(requestType.id, data);
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

                        <div className="space-y-4">
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
