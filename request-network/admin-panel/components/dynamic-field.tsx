import React, { useRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { RequestTypeParam } from "@/lib/services/admin-api";
import { Image as ImageIcon, Video, FileText, UploadCloud, X } from "lucide-react";

interface DynamicFieldProps {
    param: RequestTypeParam;
    value: any;
    onChange: (value: any) => void;
    disabled?: boolean;
}

export function DynamicField({ param, value, onChange, disabled }: DynamicFieldProps) {
    const [dragActive, setDragActive] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    };

    const handleFile = (file: File) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            // Send the base64 string
            onChange(reader.result);
        };
        reader.readAsDataURL(file);
    };

    const clearFile = () => {
        onChange("");
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    // Determine accept type for file input
    let acceptType = "*/*";
    if (param.parameter_type === "image") acceptType = "image/*";
    if (param.parameter_type === "video") acceptType = "video/*";

    const renderField = () => {
        switch (param.parameter_type) {
            case "string":
                return (
                    <Input
                        value={value || ""}
                        onChange={(e) => onChange(e.target.value)}
                        disabled={disabled}
                        placeholder={param.placeholder_key}
                        required={param.is_required}
                    />
                );

            case "integer":
                return (
                    <Input
                        type="number"
                        value={value || ""}
                        onChange={(e) => onChange(parseInt(e.target.value))}
                        disabled={disabled}
                        placeholder={param.placeholder_key}
                        required={param.is_required}
                    />
                );

            case "text":
            case "json":
                return (
                    <Textarea
                        value={value || ""}
                        onChange={(e) => onChange(e.target.value)}
                        disabled={disabled}
                        placeholder={param.placeholder_key}
                        required={param.is_required}
                        className="min-h-[100px]"
                        dir={param.parameter_type === "json" ? "ltr" : "auto"}
                    />
                );

            case "boolean":
                return (
                    <Switch
                        checked={!!value}
                        onCheckedChange={onChange}
                        disabled={disabled}
                    />
                );

            case "select":
                const options = param.validation_rules?.options || [];
                return (
                    <Select
                        value={value || ""}
                        onValueChange={onChange}
                        disabled={disabled}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder={param.placeholder_key || "انتخاب کنید"} />
                        </SelectTrigger>
                        <SelectContent>
                            {options.map((opt: string) => (
                                <SelectItem key={opt} value={opt}>
                                    {opt}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                );

            case "date":
                return (
                    <Input
                        type="date"
                        value={value || ""}
                        onChange={(e) => onChange(e.target.value)}
                        disabled={disabled}
                        required={param.is_required}
                    />
                );

            case "image":
            case "video":
            case "file":
                return (
                    <div className="space-y-4">
                        {value ? (
                            <div className="relative rounded-lg border bg-slate-50 dark:bg-slate-900 p-4 flex flex-col items-center justify-center min-h-[150px]">
                                <Button
                                    variant="destructive"
                                    size="icon"
                                    className="absolute top-2 right-2 h-8 w-8 rounded-full"
                                    onClick={clearFile}
                                    disabled={disabled}
                                    type="button"
                                >
                                    <X className="h-4 w-4" />
                                </Button>

                                {param.parameter_type === "image" && value.startsWith("data:image/") ? (
                                    <img src={value} alt="Preview" className="max-h-[200px] object-contain rounded-md" />
                                ) : param.parameter_type === "video" && value.startsWith("data:video/") ? (
                                    <video src={value} controls className="max-h-[200px] rounded-md" />
                                ) : (
                                    <div className="flex flex-col items-center gap-2 text-slate-500">
                                        <FileText className="h-10 w-10" />
                                        <span>فایل آماده ارسال است</span>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div
                                className={`flex flex-col items-center justify-center w-full min-h-[150px] border-2 border-dashed rounded-lg cursor-pointer transition-colors ${dragActive
                                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                                        : "border-gray-300 bg-gray-50 dark:border-gray-700 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800/80"
                                    } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
                                onDragEnter={disabled ? undefined : handleDrag}
                                onDragLeave={disabled ? undefined : handleDrag}
                                onDragOver={disabled ? undefined : handleDrag}
                                onDrop={disabled ? undefined : handleDrop}
                                onClick={() => !disabled && fileInputRef.current?.click()}
                            >
                                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                    {param.parameter_type === "image" ? (
                                        <ImageIcon className="w-10 h-10 mb-3 text-gray-400" />
                                    ) : param.parameter_type === "video" ? (
                                        <Video className="w-10 h-10 mb-3 text-gray-400" />
                                    ) : (
                                        <UploadCloud className="w-10 h-10 mb-3 text-gray-400" />
                                    )}
                                    <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
                                        <span className="font-semibold">برای آپلود کلیک کنید</span> یا فایل را رها کنید
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">
                                        {param.parameter_type === "image" ? "PNG, JPG" : param.parameter_type === "video" ? "MP4, WebM" : "همه نوع فایل"}
                                    </p>
                                </div>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    className="hidden"
                                    accept={acceptType}
                                    onChange={handleChange}
                                    disabled={disabled}
                                />
                            </div>
                        )}
                    </div>
                );

            default:
                return (
                    <Input
                        value={value || ""}
                        onChange={(e) => onChange(e.target.value)}
                        disabled={disabled}
                        placeholder={`نوع فیلد ناشناخته: ${param.parameter_type}`}
                        required={param.is_required}
                    />
                );
        }
    };

    return (
        <div className="space-y-2">
            <div className="flex justify-between items-center">
                <Label className={`flex items-center gap-1 ${param.is_required ? "after:content-['*'] after:text-red-500" : ""}`}>
                    {param.name}
                </Label>
                {param.description && (
                    <span className="text-xs text-muted-foreground">{param.description}</span>
                )}
            </div>
            {renderField()}
        </div>
    );
}
