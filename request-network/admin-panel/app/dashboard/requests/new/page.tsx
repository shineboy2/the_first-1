"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth-store";
import {
    ArrowRight,
    Loader2,
    Save,
    AlertCircle,
    CheckCircle2,
    Code,
    Settings2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
    CardFooter
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { requestService, requestTypeService, RequestType } from "@/lib/services/admin-api";
import { DynamicField } from "@/components/dynamic-field";

export default function NewRequestPage() {
    const router = useRouter();
    const { user: currentUser } = useAuthStore();

    // Base State
    const [name, setName] = useState("");
    const [loading, setLoading] = useState(false);
    const [initLoading, setInitLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Request Types State
    const [requestTypes, setRequestTypes] = useState<RequestType[]>([]);
    const [selectedType, setSelectedType] = useState<string>("_raw");
    const [formValues, setFormValues] = useState<Record<string, any>>({});

    // Legacy / Raw JSON State
    const [serviceName, setServiceName] = useState("");
    const [payloadJson, setPayloadJson] = useState("{\n  \"query_params\": {\n    \"param1\": \"value1\"\n  }\n}");
    const [jsonError, setJsonError] = useState<string | null>(null);

    useEffect(() => {
        loadRequestTypes();
    }, []);

    const loadRequestTypes = async () => {
        try {
            setInitLoading(true);
            // TODO: Temporary fix to enforce manual entry until request types are synced from Response Network
            setRequestTypes([]);
            setSelectedType("_raw");
            setServiceName("");
        } catch (err) {
            console.error("Error loading request types:", err);
        } finally {
            setInitLoading(false);
        }
    };

    const validateJson = (val: string) => {
        try {
            JSON.parse(val);
            setJsonError(null);
            return true;
        } catch (e) {
            setJsonError("فرمت JSON وارد شده نامعتبر است!");
            return false;
        }
    };

    const handlePayloadChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const val = e.target.value;
        setPayloadJson(val);
        validateJson(val);
    };

    const handleTypeChange = (val: string) => {
        setSelectedType(val);
        setFormValues({}); // Reset form values on type change

        if (val !== "_raw") {
            const rt = requestTypes.find(t => t.name === val);
            if (rt) {
                setServiceName(val); // Auto-fill service name
            }
        }
    };

    const handleFieldValueChange = (key: string, value: any) => {
        setFormValues(prev => ({ ...prev, [key]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!name.trim()) {
            setError("لطفاً یک نام (عنوان) برای درخواست وارد کنید.");
            return;
        }

        let fieldRequest: any = {};
        const isRawMode = selectedType === "_raw";

        if (isRawMode) {
            if (!serviceName.trim()) {
                setError("لطفاً نام سرویس (Query Type) را در حالت دستی وارد کنید.");
                return;
            }
            if (!validateJson(payloadJson)) {
                setError("لطفا خطاهای مربوط به فرمت JSON را برطرف کنید.");
                return;
            }
            fieldRequest = JSON.parse(payloadJson);
        } else {
            // Dynamic form validation
            const currentType = requestTypes.find(t => t.name === selectedType);
            if (!currentType) {
                setError("نوع درخواست نامعتبر است.");
                return;
            }

            // Check required fields
            const missingRequired = currentType.parameters.filter(
                p => p.is_required && (formValues[p.placeholder_key] === undefined || formValues[p.placeholder_key] === "")
            );

            if (missingRequired.length > 0) {
                setError(`لطفا فیلدهای اجباری زیر را پر کنید: ${missingRequired.map(p => p.name).join('، ')}`);
                return;
            }

            fieldRequest = { ...formValues };
        }

        try {
            setLoading(true);
            setError(null);

            const requestData = {
                name: name.trim(),
                reqState: "pending",
                request: {
                    serviceName: isRawMode ? serviceName.trim() : selectedType,
                    fieldRequest: fieldRequest
                }
            };

            await requestService.createRequest(requestData);
            router.push("/dashboard/requests");

        } catch (err: any) {
            console.error("Error submitting request:", err);
            setError(err?.response?.data?.detail || "خطا در ثبت درخواست. لطفاً دوباره تلاش کنید.");
        } finally {
            setLoading(false);
        }
    };

    if (!currentUser) return null;

    const currentTypeConfig = requestTypes.find(t => t.name === selectedType);

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-12">
            {/* Header */}
            <div className="border-b bg-white dark:bg-gray-800">
                <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="icon" onClick={() => router.push("/dashboard/requests")}>
                            <ArrowRight className="h-5 w-5" />
                        </Button>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                                ثبت درخواست جدید
                            </h1>
                            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                پر کردن فرم و ارسال درخواست به شبکه ایزوله
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
                {error && (
                    <Alert variant="destructive" className="mb-6">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>خطا در ثبت</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="space-y-6">
                        {/* Title Card */}
                        <Card className="border-t-4 border-t-blue-500 shadow-sm">
                            <CardHeader className="pb-4">
                                <CardTitle>عنوان درخواست</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <Input
                                    id="name"
                                    placeholder="مثال: استعلام کاربر ۱۲۳۴۵"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    disabled={loading}
                                    className="max-w-md"
                                />
                            </CardContent>
                        </Card>

                        {/* Query Configuration Card */}
                        <Card className="shadow-sm">
                            <CardHeader className="pb-4 border-b bg-slate-50 dark:bg-slate-800">
                                <CardTitle className="text-lg flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Settings2 className="h-5 w-5 text-gray-500" />
                                        نوع و اطلاعات درخواست
                                    </div>
                                    <div className="w-1/2 max-w-[250px]">
                                        {initLoading ? (
                                            <div className="flex items-center text-sm text-gray-500">
                                                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                                                در حال بارگذاری انواع درخواست...
                                            </div>
                                        ) : (
                                            <Select value={selectedType} onValueChange={handleTypeChange} disabled={loading}>
                                                <SelectTrigger className="w-full bg-white dark:bg-slate-900 border-blue-200 focus:ring-blue-500">
                                                    <SelectValue placeholder="انتخاب نوع درخواست" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {requestTypes.map(rt => (
                                                        <SelectItem key={rt.name} value={rt.name}>
                                                            {rt.name}
                                                        </SelectItem>
                                                    ))}
                                                    <SelectItem value="_raw" className="border-t mt-1 font-semibold text-gray-600">
                                                        (ورود دستی JSON)
                                                    </SelectItem>
                                                </SelectContent>
                                            </Select>
                                        )}
                                    </div>
                                </CardTitle>
                                {currentTypeConfig && (
                                    <CardDescription className="pt-2">
                                        {currentTypeConfig.description || "توضیحاتی برای این نوع درخواست ثبت نشده است."}
                                    </CardDescription>
                                )}
                            </CardHeader>
                            <CardContent className="pt-6">
                                {selectedType === "_raw" ? (
                                    // Legacy / Raw JSON Form
                                    <div className="space-y-6">
                                        <div className="space-y-2">
                                            <Label htmlFor="serviceName">نام سرویس (Service Name)</Label>
                                            <Input
                                                id="serviceName"
                                                placeholder="مثال: standard_request"
                                                value={serviceName}
                                                onChange={(e) => setServiceName(e.target.value)}
                                                disabled={loading}
                                                dir="ltr"
                                                className="max-w-md"
                                            />
                                            <p className="text-xs text-muted-foreground mr-1">باید یک آیدی سرویس معتبر در شبکه پاسخ باشد.</p>
                                        </div>

                                        <div className="space-y-2 pt-2">
                                            <div className="flex justify-between items-center">
                                                <Label htmlFor="payload">پارامترهای ورودی (JSON Payload)</Label>
                                                {jsonError ? (
                                                    <Badge variant="destructive">{jsonError}</Badge>
                                                ) : (
                                                    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">فرمت صحیح</Badge>
                                                )}
                                            </div>
                                            <div className="relative">
                                                <Textarea
                                                    id="payload"
                                                    className="font-mono text-sm leading-relaxed min-h-[250px] bg-slate-950 text-green-400 p-4"
                                                    dir="ltr"
                                                    value={payloadJson}
                                                    onChange={handlePayloadChange}
                                                    disabled={loading}
                                                />
                                                <Code className="absolute top-4 right-4 h-5 w-5 opacity-20 text-white pointer-events-none" />
                                            </div>
                                        </div>
                                    </div>
                                ) : currentTypeConfig ? (
                                    // Dynamic Generated Form from Schema
                                    <div className="space-y-6">
                                        {currentTypeConfig.parameters && currentTypeConfig.parameters.length > 0 ? (
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
                                                {currentTypeConfig.parameters.map((param) => (
                                                    <div key={param.placeholder_key} className={
                                                        ["text", "json", "image", "video", "file"].includes(param.parameter_type) ? "md:col-span-2" : ""
                                                    }>
                                                        <DynamicField
                                                            param={param}
                                                            value={formValues[param.placeholder_key]}
                                                            onChange={(val) => handleFieldValueChange(param.placeholder_key, val)}
                                                            disabled={loading}
                                                        />
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="flex flex-col items-center justify-center py-10 text-gray-500">
                                                <AlertCircle className="h-10 w-10 mb-2 opacity-20" />
                                                <p>این نوع درخواست پارامتر ورودی ندارد.</p>
                                                <p className="text-sm mt-1">با ثبت فرم، درخواست مستقیماً اجرا می‌شود.</p>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="text-center py-12 text-gray-400">
                                        نوع درخواست را از منوی بالا انتخاب کنید.
                                    </div>
                                )}
                            </CardContent>
                            <CardFooter className="bg-gray-50 dark:bg-gray-800/50 flex justify-end gap-3 px-6 py-4 border-t">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => router.push("/dashboard/requests")}
                                    disabled={loading}
                                >
                                    انصراف
                                </Button>
                                <Button
                                    type="submit"
                                    disabled={loading || (selectedType === "_raw" && (!!jsonError || !serviceName)) || !name}
                                    className="min-w-[120px]"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            در حال ثبت...
                                        </>
                                    ) : (
                                        <>
                                            <Save className="mr-2 h-4 w-4" />
                                            ثبت و ارسال
                                        </>
                                    )}
                                </Button>
                            </CardFooter>
                        </Card>
                    </div>
                </form>
            </div>
        </div>
    );
}
