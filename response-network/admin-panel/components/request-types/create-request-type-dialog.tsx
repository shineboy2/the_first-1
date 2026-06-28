"use client";

import { useState } from "react";
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
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
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
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Loader2 } from "lucide-react";
import { requestService } from "@/lib/services/admin-api";

const createRequestTypeSchema = z.object({
    name: z.string().min(1, "نام الزامی است"),
    description: z.string().optional(),
    is_active: z.boolean().default(false),
});

type CreateRequestTypeFormData = z.infer<typeof createRequestTypeSchema>;

interface CreateRequestTypeDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

export function CreateRequestTypeDialog({
    open,
    onOpenChange,
    onSuccess,
}: CreateRequestTypeDialogProps) {
    const [isLoading, setIsLoading] = useState(false);

    const form = useForm<CreateRequestTypeFormData>({
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        resolver: zodResolver(createRequestTypeSchema) as any,
        defaultValues: {
            name: "",
            description: "",
            is_active: false,
        },
    });

    const onSubmit = async (data: CreateRequestTypeFormData) => {
        try {
            setIsLoading(true);
            await requestService.createRequestType(data);
            form.reset();
            onSuccess();
            onOpenChange(false);
        } catch (error) {
            console.error("Error creating request type:", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>ایجاد نوع درخواست جدید</DialogTitle>
                    <DialogDescription>
                        یک نوع درخواست جدید برای سیستم تعریف کنید
                    </DialogDescription>
                </DialogHeader>

                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                        <FormField
                            control={form.control}
                            name="name"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>نام نوع درخواست</FormLabel>
                                    <FormControl>
                                        <Input placeholder="مثال: تحلیل متن" {...field} />
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
                                        <Textarea
                                            placeholder="توضیحات مختصر در مورد این نوع درخواست"
                                            {...field}
                                        />
                                    </FormControl>
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
                                {isLoading && <Loader2 className="ml-2 h-4 w-4 animate-spin" />}
                                ایجاد
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
