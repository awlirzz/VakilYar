# --- مرحله ۱: Builder ---
# در این مرحله، کد پایتون به یک فایل اجرایی کامپایل می‌شود
FROM python:3.10-slim as builder

# نصب نیازمندی‌های سیستمی (شامل ffmpeg برای پردازش صوت و build-essential برای کامپایل)
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# نصب نیازمندی‌های پایتون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن سورس کد پروژه
COPY . .

# کامپایل کردن اپلیکیشن با Nuitka
# --standalone: تمام نیازمندی‌ها را در خروجی کپی می‌کند
# --onefile: یک فایل اجرایی تکی میسازد
# --output-dir: پوشه‌ای که خروجی در آن ذخیره می‌شود
RUN python -m nuitka --onefile --output-dir=dist app.py

# --- مرحله ۲: Final ---
# در این مرحله، فقط فایل اجرایی کامپایل شده به یک ایمیج نهایی سبک منتقل می‌شود
FROM python:3.10-slim

# نصب نیازمندی‌های سیستمی حداقلی که برای اجرای برنامه لازم است
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# کپی کردن فایل اجرایی کامپایل شده از مرحله Builder
COPY --from=builder /app/dist/app.bin .

# پورت 5000 را برای دسترسی به سرور باز کن
EXPOSE 5000

# دستور اجرای برنامه کامپایل شده
CMD ["./app.bin"]