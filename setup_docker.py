import os

# دیکشنری حاوی نام فایل‌ها و محتوای آن‌ها
files_to_create = {
    ".env.example": """
# کلید API خود را که از پلتفرم OpenAI دریافت کرده‌اید، اینجا قرار دهید
# فایل .env اصلی نباید در git یا هر سیستم ورژن کنترل دیگری قرار گیرد

OPENAI_API_KEY="sk-YourSecretApiKeyGoesHere"
""",

    ".gitignore": """
# Environment variables
.env

# Python cache
__pycache__/
*.pyc

# Docker
dist/
    """,

    "Dockerfile": """
# --- مرحله ۱: Builder ---
# در این مرحله، کد پایتون به یک فایل اجرایی کامپایل می‌شود
FROM python:3.12-slim as builder

# نصب نیازمندی‌های سیستمی (شامل ffmpeg برای پردازش صوت و build-essential برای کامپایل)
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    ffmpeg \\
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
FROM python:3.12-slim

# نصب نیازمندی‌های سیستمی حداقلی که برای اجرای برنامه لازم است
RUN apt-get update && apt-get install -y --no-install-recommends \\
    ffmpeg \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# کپی کردن فایل اجرایی کامپایل شده از مرحله Builder
COPY --from=builder /app/dist/app.bin .

# پورت 5000 را برای دسترسی به سرور باز کن
EXPOSE 5000

# دستور اجرای برنامه کامپایل شده
CMD ["./app.bin"]
""",

    "docker-compose.yml": """
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    volumes:
      # این volume برای دیباگ فایل‌های صوتی است که در کد تعریف شده بود
      # اگر نیاز به ذخیره دائمی آن‌ها ندارید، می‌توانید این بخش را حذف کنید
      - /tmp/problematic_audio_files:/tmp/problematic_audio_files
"""
}

def create_files():
    """فایل‌های جدید را ایجاد می‌کند."""
    for filename, content in files_to_create.items():
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            print(f"✅  فایل '{filename}' با موفقیت ایجاد شد.")
        except IOError as e:
            print(f"❌  خطا در ایجاد فایل '{filename}': {e}")

def update_requirements():
    """فایل نیازمندی‌ها را به‌روزرسانی می‌کند."""
    try:
        with open('requirements.txt', 'a', encoding='utf-8') as f:
            f.write("\npython-dotenv>=0.21\nNuitka>=1.8\n")
        print("✅  فایل 'requirements.txt' با موفقیت به‌روزرسانی شد.")
    except IOError as e:
        print(f"❌  خطا در به‌روزرسانی 'requirements.txt': {e}")

def update_core_py():
    """فایل backend/core.py را برای خواندن کلید از متغیرهای محیطی اصلاح می‌کند."""
    filepath = os.path.join('backend', 'core.py')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # خط مربوط به دریافت کلید API را جایگزین می‌کند
        old_line = 'openai.api_key = os.getenv("api_key")'
        new_line = 'openai.api_key = os.getenv("OPENAI_API_KEY")'
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅  فایل 'backend/core.py' با موفقیت به‌روزرسانی شد.")
        else:
            print("⚠️  هشدار: خط مورد نظر برای جایگزینی در 'backend/core.py' یافت نشد.")

    except FileNotFoundError:
        print(f"❌  خطا: فایل '{filepath}' یافت نشد.")
    except IOError as e:
        print(f"❌  خطا در ویرایش فایل '{filepath}': {e}")

def update_app_py():
    """کتابخانه python-dotenv را به app.py اضافه می‌کند."""
    filepath = 'app.py'
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # اضافه کردن ایمپورت‌ها در ابتدای فایل
        new_lines = [
            'from dotenv import load_dotenv\n',
            'load_dotenv()\n\n'
        ]
        
        # جلوگیری از اضافه شدن مجدد در صورت اجرای دوباره اسکریپت
        if not lines[0].strip().startswith('from dotenv'):
            lines = new_lines + lines
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print("✅  فایل 'app.py' با موفقیت به‌روزرسانی شد.")
        else:
             print("ℹ️  فایل 'app.py' قبلاً به‌روزرسانی شده است.")

    except FileNotFoundError:
        print(f"❌  خطا: فایل '{filepath}' یافت نشد.")
    except IOError as e:
        print(f"❌  خطا در ویرایش فایل '{filepath}': {e}")


if __name__ == "__main__":
    print("شروع فرآیند ایجاد و به‌روزرسانی فایل‌ها...")
    create_files()
    update_requirements()
    update_core_py()
    update_app_py()
    print("\n🎉  تمام عملیات با موفقیت انجام شد!")
    print("اکنون می‌توانید فایل .env.example را به .env تغییر نام داده و کلید API خود را در آن قرار دهید.")