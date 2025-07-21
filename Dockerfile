# --- ایمیج پایه ---
# استفاده از یک ایمیج رسمی و بهینه پایتون
FROM python:3.10-slim

# --- نصب نیازمندی‌های سیستمی ---
# فقط ffmpeg برای پردازش صوت مورد نیاز است
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# --- تنظیم محیط کاری ---
WORKDIR /app

# --- نصب نیازمندی‌های پایتون ---
# ابتدا فایل نیازمندی‌ها را کپی و نصب می‌کنیم تا از کش داکر بهتر استفاده شود
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- کپی کردن سورس کد ---
# تمام کدهای پروژه را به کانتینر منتقل می‌کنیم
COPY . .

# --- اجرای برنامه ---
# پورت 5000 را برای دسترسی به سرور باز می‌کنیم
EXPOSE 5000

# برنامه را با استفاده از مفسر پایتون اجرا می‌کنیم
CMD ["python", "app.py"]