# -------------------- STAGE 1: The Builder --------------------
# این مرحله تمام ابزارهای لازم برای کامپایل را نصب کرده و برنامه پایتون را به یک فایل اجرایی تبدیل می‌کند
FROM python:3.10-slim AS builder

# نصب وابستگی‌های سیستمی برای کامپایل
# build-essential شامل کامپایلر C (مانند GCC) است که برای Nuitka ضروری است
# ffmpeg همچنان نصب می‌شود تا اگر وابستگی‌ها در حین نصب به آن نیاز داشتند، مشکلی پیش نیاید
RUN apt-get update && apt-get install -y --no-install-recommends build-essential ffmpeg

# تنظیم دایرکتوری کاری
WORKDIR /app

# نصب Nuitka و وابستگی‌های پروژه
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir nuitka
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن کدهای برنامه
COPY . .

# اجرای Nuitka برای کامپایل کردن برنامه
# --standalone: تمام کتابخانه‌های مورد نیاز را در کنار فایل اجرایی قرار می‌دهد
# --output-dir=dist: خروجی را در پوشه‌ی dist قرار می‌دهد
RUN python -m nuitka --standalone --output-dir=dist app.py


# -------------------- STAGE 2: The Runner --------------------
# این مرحله نهایی و بسیار سبک است و فقط فایل‌های کامپایل شده را اجرا می‌کند
FROM python:3.10-slim

# نصب وابستگی‌های سیستمی که در زمان اجرا نیاز هستند (نه برای کامپایل)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# تنظیم دایرکتوری کاری
WORKDIR /app

# تنظیم متغیرهای محیطی
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# کپی کردن فایل‌های کامپایل شده از مرحله Builder
# فقط پوشه dist (که حاوی فایل اجرایی و کتابخانه‌هایش است) کپی می‌شود
COPY --from=builder /app/dist .

# باز کردن پورت برنامه
EXPOSE 5000

# اجرای برنامه کامپایل شده
# به جای "python app.py"، فایل اجرایی ساخته شده توسط Nuitka را اجرا می‌کنیم
CMD ["./app.bin"]