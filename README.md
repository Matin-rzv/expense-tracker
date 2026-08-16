# اپ دخل و خرج

نسخه اول Personal expense tracker با:
- Python
- Streamlit
- Supabase/PostgreSQL
- Plotly
- Pandas

## امکانات
- ثبت درآمد و هزینه
- دسته‌بندی هزینه‌ها
- داشبورد ماهانه
- محاسبه درآمد، هزینه، موجودی و نرخ پس‌انداز
- گزارش ماهانه
- نمودار دایره‌ای هزینه‌ها
- نمودار مقایسه ماه‌ها
- نمودار روند هزینه روزانه
- جستجو و فیلتر تراکنش‌ها
- ویرایش و حذف
- خروجی CSV و Excel
- رابط ساده و مناسب موبایل/iPhone

## راه‌اندازی محلی

```bash
pip install -r requirements.txt
streamlit run app.py
```

سپس فایل `.streamlit/secrets.toml` را بساز و مقادیر Supabase را داخل آن قرار بده.

## ساخت دیتابیس

در Supabase > SQL Editor، محتوای `schema.sql` را اجرا کن.

## Deploy روی Streamlit Community Cloud

1. پروژه را در GitHub قرار بده.
2. در Streamlit Community Cloud یک App جدید بساز.
3. فایل اصلی را `app.py` انتخاب کن.
4. در بخش Secrets این دو مقدار را وارد کن:

```toml
SUPABASE_URL = "..."
SUPABASE_SERVICE_ROLE_KEY = "..."
```

بعد لینک اپ را روی iPhone با Safari باز کن.

## نکته امنیتی

`SUPABASE_SERVICE_ROLE_KEY` را هرگز داخل GitHub قرار نده.
این کلید فقط باید در Streamlit Secrets باشد.

## نکته درباره iPhone

این برنامه یک Web App است؛ بنابراین نیازی به نصب Python روی iPhone ندارد.
با Safari یا Chrome باز می‌شود و رابط برای صفحه کوچک طراحی شده است.


## UI language and currency
The application UI is in English. All monetary values are displayed in Toman.
