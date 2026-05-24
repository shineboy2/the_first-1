# ✅ بازطراحی مدیریت دسترسی External API

## تاریخ: 2026-04-27

---

## 🎯 تغییرات انجام شده

### ❌ حذف شد
- صفحه جداگانه `/dashboard/external-api-access` حذف شد
- منوی "دسترسی API خارجی" از sidebar حذف شد

### ✅ اضافه شد
- دکمه "مدیریت دسترسی" در منوی عملیات هر API در صفحه External APIs
- Dialog مدیریت دسترسی مشابه Request Types
- Component جدید: `ManageAccessDialog` برای External APIs

---

## 📋 ساختار جدید

### صفحه External APIs
**مسیر**: `/dashboard/external-apis`

**منوی عملیات هر API**:
1. ✏️ ویرایش
2. 👥 **مدیریت دسترسی** (جدید)
3. 🗑️ حذف

### Dialog مدیریت دسترسی
**Component**: `components/external-apis/manage-access-dialog.tsx`

**ویژگی‌ها**:
- نمایش لیست Profile Types که دسترسی دارند
- فرم اضافه کردن دسترسی جدید
- دکمه حذف دسترسی برای هر Profile Type
- Alert برای خطا و موفقیت
- راهنمای استفاده

**عملکرد**:
1. دریافت لیست همه Profile Types
2. دریافت دسترسی فعلی هر Profile Type
3. نمایش Profile Types که دسترسی دارند
4. امکان اضافه کردن Profile Type جدید
5. امکان حذف دسترسی

---

## 🔧 فایل‌های تغییر یافته

### 1. صفحه External APIs
**فایل**: `response-network/admin-panel/app/dashboard/external-apis/page.tsx`

**تغییرات**:
- Import کردن `ManageAccessDialog`
- اضافه کردن state `manageAccessDialogOpen`
- اضافه کردن منوی "مدیریت دسترسی" در dropdown
- اضافه کردن Dialog در انتها

```tsx
// Import
import { ManageAccessDialog } from "@/components/external-apis/manage-access-dialog";

// State
const [manageAccessDialogOpen, setManageAccessDialogOpen] = useState(false);

// Menu Item
<DropdownMenuItem onClick={() => {
    setSelectedApi(api);
    setManageAccessDialogOpen(true);
}}>
    <Users className="ml-2 h-4 w-4" />
    مدیریت دسترسی
</DropdownMenuItem>

// Dialog
<ManageAccessDialog
    open={manageAccessDialogOpen}
    onOpenChange={setManageAccessDialogOpen}
    onSuccess={fetchExternalAPIs}
    externalApi={selectedApi}
/>
```

### 2. Component جدید
**فایل**: `response-network/admin-panel/components/external-apis/manage-access-dialog.tsx`

**ساختار**:
```tsx
interface ManageAccessDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
    externalApi: ExternalAPI | null;
}

export function ManageAccessDialog({ ... }) {
    // States
    const [profileTypes, setProfileTypes] = useState<ProfileType[]>([]);
    const [profileAccess, setProfileAccess] = useState<ProfileAccess[]>([]);
    
    // Functions
    const handleGrantAccess = async () => { ... }
    const handleRevokeAccess = async (profileType: string) => { ... }
    
    // UI
    return (
        <Dialog>
            {/* Form اضافه کردن */}
            {/* Table لیست دسترسی‌ها */}
        </Dialog>
    );
}
```

### 3. Layout
**فایل**: `response-network/admin-panel/app/dashboard/layout.tsx`

**تغییرات**:
- حذف منوی "دسترسی API خارجی"

---

## 🎨 UI/UX

### قبل
```
Sidebar:
├── API‌های خارجی
├── دسترسی API خارجی  ← صفحه جداگانه
└── ...

صفحه External APIs:
└── عملیات: ویرایش | حذف
```

### بعد
```
Sidebar:
├── API‌های خارجی
└── ...

صفحه External APIs:
└── عملیات: ویرایش | مدیریت دسترسی | حذف
                      ↓
                   Dialog مدیریت دسترسی
```

---

## 🔄 فرایند مدیریت دسترسی

### مراحل:
1. کاربر به صفحه External APIs می‌رود
2. روی منوی عملیات یک API کلیک می‌کند
3. گزینه "مدیریت دسترسی" را انتخاب می‌کند
4. Dialog باز می‌شود و لیست Profile Types با دسترسی نمایش داده می‌شود
5. می‌تواند Profile Type جدید اضافه کند
6. می‌تواند دسترسی موجود را حذف کند
7. تغییرات بلافاصله اعمال می‌شوند

### API Calls:
```typescript
// دریافت دسترسی یک Profile Type
GET /api/v1/external-apis/profile-types/{profile_type}/access

// به‌روزرسانی دسترسی
PATCH /api/v1/external-apis/profile-types/{profile_type}/access
Body: { allowed_external_apis: ["api1", "api2"] }
```

---

## ✅ مزایای طراحی جدید

### 1. سازگاری با Request Types
- مدیریت دسترسی External APIs حالا دقیقاً مثل Request Types است
- کاربر نیازی به یادگیری رابط جدید ندارد

### 2. کاهش پیچیدگی
- یک صفحه کمتر در منو
- دسترسی مستقیم از همان صفحه API ها
- کمتر کلیک برای مدیریت دسترسی

### 3. Context بهتر
- وقتی روی "مدیریت دسترسی" کلیک می‌کنید، می‌دانید برای کدام API است
- نام API در عنوان Dialog نمایش داده می‌شود

### 4. تمیزتر
- منوی sidebar شلوغ‌تر نیست
- همه عملیات مربوط به یک API در یک جا هستند

---

## 🚀 Deploy

### فایل‌های منتقل شده:
```bash
# Component جدید
components/external-apis/manage-access-dialog.tsx

# صفحه آپدیت شده
app/dashboard/external-apis/page.tsx

# Layout آپدیت شده
app/dashboard/layout.tsx
```

### فایل‌های حذف شده:
```bash
# صفحه قدیمی
app/dashboard/external-api-access/page.tsx (حذف شد)
```

### Rebuild:
```bash
docker compose up --build -d admin-panel
```

**وضعیت**: ✅ Deploy شد و در حال اجرا است

---

## 📝 تست

### مراحل تست:
1. ✅ ورود به `/dashboard/external-apis`
2. ✅ کلیک روی منوی عملیات یک API
3. ✅ انتخاب "مدیریت دسترسی"
4. ✅ باز شدن Dialog
5. ✅ نمایش لیست Profile Types با دسترسی
6. ✅ اضافه کردن Profile Type جدید
7. ✅ حذف دسترسی موجود
8. ✅ بستن Dialog و بازگشت به لیست

### URL تست:
```
http://192.168.214.141:3000/dashboard/external-apis
```

---

## 🎯 نتیجه

✅ مدیریت دسترسی External API حالا دقیقاً مثل Request Types است
✅ صفحه جداگانه حذف شد
✅ UI ساده‌تر و سازگارتر شد
✅ همه تغییرات deploy شدند

---

## 📚 مستندات مرتبط

- `EXTERNAL_API_IMPLEMENTATION_COMPLETE.md` - پیاده‌سازی اولیه
- `EXTERNAL_API_TODO_CRITICAL.md` - TODO های قبلی
- `response-network/admin-panel/components/request-types/manage-access-dialog.tsx` - الگوی مرجع

