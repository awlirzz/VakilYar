"""
audio_handler – تبدیل فایل WAV (≤30s) به متن فارسی
استفاده از مدل gpt-4o-mini-transcribe
"""
import tempfile
import os
import time 
import shutil # برای کپی کردن فایل (برای دیباگ)
from typing import Final
from werkzeug.datastructures import FileStorage
import openai
from pydub import AudioSegment, exceptions as pydub_exceptions

STT_MODEL: Final[str] = "gpt-4o-mini-transcribe"
MAX_DURATION_S: Final[int] = 30

# مسیر برای ذخیره فایل‌های صوتی مشکل‌دار (برای دیباگ)
# مطمئن شوید که این دایرکتوری وجود دارد و قابل نوشتن توسط کاربر Flask است.
DEBUG_AUDIO_PATH = "/tmp/problematic_audio_files/" 
# ایجاد دایرکتوری دیباگ اگر وجود ندارد
if not os.path.exists(DEBUG_AUDIO_PATH):
    try:
        os.makedirs(DEBUG_AUDIO_PATH, exist_ok=True) # exist_ok=True از خطا جلوگیری می‌کند اگر دایرکتوری از قبل وجود داشته باشد
        print(f"Debug directory ensured: {DEBUG_AUDIO_PATH}")
    except OSError as e:
        print(f"Warning: Could not create/ensure debug directory {DEBUG_AUDIO_PATH}: {e}. Debug files will not be saved.")
        DEBUG_AUDIO_PATH = None # غیرفعال کردن ذخیره فایل دیباگ در صورت خطا

class TranscriptionError(RuntimeError):
    """Raised when STT fails or input invalid."""


def _validate_and_get_audio_segment(file: FileStorage) -> AudioSegment:
    """Validates the uploaded file and returns an AudioSegment."""
    # دیگر به mimetype برای تصمیم‌گیری اولیه اتکا نمی‌کنیم، اجازه می‌دهیم pydub تشخیص دهد
    print(f"Received file: '{file.filename}', mimetype reported by client: '{file.mimetype}'")

    audio = None 
    temp_path = None # برای نگهداری مسیر فایل موقت که ایجاد و سپس حذف می‌شود

    try:
        # --- همیشه فایل را ابتدا در یک مکان موقت ذخیره می‌کنیم ---
        # این کار پایداری بیشتری نسبت به خواندن مستقیم از استریم FileStorage دارد
        # و به ما اجازه می‌دهد فایل را برای دیباگ کپی کنیم.
        
        # قبل از ذخیره، پوینتر را به ابتدا برگردانید (اگر FileStorage از آن پشتیبانی کند)
        if hasattr(file, 'seek') and callable(file.seek):
            try:
                file.seek(0)
            except Exception as e_seek:
                print(f"Warning: Could not seek on input filestream '{file.filename}': {e_seek}")

        # ایجاد فایل موقت. پسوند را .webm یا .oga می‌گذاریم تا pydub/ffmpeg بهتر حدس بزند،
        # یا حتی بدون پسوند و اجازه دهیم ffmpeg کاملا از محتوا تشخیص دهد.
        # برای سازگاری بیشتر، فعلا بدون پسوند خاص ذخیره می‌کنیم.
        fd, temp_path = tempfile.mkstemp(suffix=".dat") # .dat یا حتی بدون پسوند
        os.close(fd)
        
        file.save(temp_path)
        print(f"Saved uploaded file '{file.filename}' to temp file '{temp_path}'.")

        if not os.path.isfile(temp_path) or os.path.getsize(temp_path) == 0:
            raise TranscriptionError(f"فایل موقت در مسیر {temp_path} پس از ذخیره‌سازی ایجاد نشد یا خالی است.")
        
        # ---- بخش دیباگ: کپی کردن فایل موقت برای بررسی دستی ----
        if DEBUG_AUDIO_PATH:
            try:
                # برای نام فایل دیباگ، از نام فایل موقت و یک پسوند عمومی استفاده می‌کنیم
                # یا پسوندی که از mimetype حدس می‌زنیم (مثلا .webm اگر mimetype شامل آن باشد)
                debug_file_ext = ".bin" # پسوند عمومی
                if 'webm' in (file.mimetype or ""): debug_file_ext = ".webm"
                elif 'ogg' in (file.mimetype or ""): debug_file_ext = ".ogg"
                
                debug_file_name = f"{os.path.basename(temp_path)}-{file.filename}{debug_file_ext}"
                debug_file_copy_path = os.path.join(DEBUG_AUDIO_PATH, debug_file_name)
                shutil.copy2(temp_path, debug_file_copy_path)
                print(f"DEBUG: Copied temp file to '{debug_file_copy_path}' for inspection.")
            except Exception as e_copy:
                print(f"DEBUG: Failed to copy temp file for inspection: {e_copy}")
        # ---- پایان بخش دیباگ ----

        # به pydub اجازه دهید فرمت را از محتوای فایل تشخیص دهد
        # از from_file استفاده کنید و format را مشخص نکنید
        print(f"Attempting to load audio from '{temp_path}' with pydub (auto-detect format).")
        audio = AudioSegment.from_file(temp_path) 
        print(f"Successfully loaded audio from '{temp_path}'. Detected duration: {audio.duration_seconds:.2f}s")

    except pydub_exceptions.CouldntDecodeError as e_decode:
        # این خطا معمولا زمانی رخ می‌دهد که ffmpeg نتواند فایل را بخواند
        raise TranscriptionError(f"خطا در رمزگشایی فایل صوتی '{file.filename}' (ذخیره شده در '{temp_path}'): {e_decode}. "
                                 "ممکن است فایل خراب باشد یا فرمت آن توسط ffmpeg پشتیبانی نشود.")
    except Exception as e_process:
        raise TranscriptionError(f"خطا در پردازش فایل صوتی '{file.filename}': {type(e_process).__name__} - {e_process}")
    finally:
        # فایل موقت اصلی را اگر ایجاد شده بود پاک کن
        if temp_path and os.path.exists(temp_path):
            try: 
                os.unlink(temp_path)
                print(f"Temp file {temp_path} deleted.")
            except Exception as e_unlink_finally:
                 print(f"Warning: Could not delete temp file {temp_path} in finally: {e_unlink_finally}")
        
        # استریم فایل ورودی را ببند (اگر هنوز باز است و قابل بستن)
        if hasattr(file, 'close') and callable(file.close) and not file.closed:
            try: 
                file.close()
                print(f"Input filestream '{file.filename}' closed.")
            except Exception as e_close_finally:
                print(f"Warning: Could not close input filestream '{file.filename}': {e_close_finally}")

    # --- اعتبارسنجی نهایی و بازگشت ---
    if audio is None:
        # این نباید اتفاق بیفتد اگر کد بالا به درستی اجرا شود و خطاها را پرتاب کند
        raise TranscriptionError("پردازش فایل صوتی با شکست مواجه شد و شیء صوتی ایجاد نشد.")

    dur = audio.duration_seconds
    if dur > MAX_DURATION_S:
        raise TranscriptionError(f"طول فایل '{file.filename}' ({dur:.2f}s) نباید بیش از {MAX_DURATION_S} ثانیه باشد.")
    
    print(f"File '{file.filename}' validated. Duration: {dur:.2f}s")
    return audio


def transcribe(file: FileStorage) -> str:
    """Main API: FileStorage → str transcript (fa)."""
    temp_wav_for_openai = None # مسیری برای فایل موقت که به OpenAI ارسال می‌شود
    try:
        audio_segment = _validate_and_get_audio_segment(file)
        
        # AudioSegment را در یک فایل WAV موقت (فرمت استاندارد PCM) برای ارسال به OpenAI ذخیره کنید
        fd, temp_wav_for_openai = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        # export با فرمت wav، فایل را به یک WAV استاندارد تبدیل می‌کند
        audio_segment.export(temp_wav_for_openai, format="wav")
        print(f"AudioSegment exported to temp WAV file for OpenAI: {temp_wav_for_openai}")

        if not os.path.isfile(temp_wav_for_openai) or os.path.getsize(temp_wav_for_openai) == 0:
            raise TranscriptionError(f"فایل WAV موقت برای OpenAI در مسیر {temp_wav_for_openai} ایجاد نشد یا خالی است.")

        print(f"Proceeding to OpenAI transcription with file: {temp_wav_for_openai}")
        with open(temp_wav_for_openai, "rb") as f_audio:
            resp = openai.Audio.transcribe(
                file=f_audio,
                model=STT_MODEL,
                response_format="text",
                language="fa",
            )

        if not resp:
            raise TranscriptionError("مدل هیچ متنی برنگرداند.")
        
        return str(resp).strip()

    except Exception as e:
        print(f"ERROR in transcribe function: {type(e).__name__}: {e}")
        if not isinstance(e, TranscriptionError):
            raise TranscriptionError(f"خطا در تبدیل گفتار: {type(e).__name__} - {e}") from e
        else:
            raise

    finally:
        if temp_wav_for_openai and os.path.exists(temp_wav_for_openai):
            try:
                os.unlink(temp_wav_for_openai)
                print(f"Successfully deleted temp file for OpenAI: {temp_wav_for_openai} in transcribe's finally block.")
            except Exception as unlink_error:
                print(f"WARNING: Could not delete temp file for OpenAI {temp_wav_for_openai} in transcribe's finally block: {unlink_error}")

