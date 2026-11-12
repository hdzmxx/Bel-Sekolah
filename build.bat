@echo off
REM Membuat BelSekolah.exe (satu berkas, tanpa jendela konsol).
REM Untuk Windows 7 gunakan Python 3.8.x (32-bit) dan PyInstaller 5.13.2.
python -m pip install pyinstaller==5.13.2
python -m PyInstaller --noconsole --onefile --name BelSekolah bel_sekolah.py
echo.
echo Selesai. Hasil ada di folder dist\BelSekolah.exe
pause
