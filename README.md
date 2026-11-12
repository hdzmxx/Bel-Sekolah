# Bel Sekolah Otomatis

Aplikasi desktop untuk membunyikan bel sekolah secara otomatis sesuai jadwal.
Ditulis dengan Python + Tkinter, tanpa perlu memasang paket tambahan di Windows.


## Unduh

- **[Unduh BelSekolah.exe](https://github.com/hdzmxx/Bel-Sekolah/releases/latest/download/BelSekolah.exe)** (langsung mengunduh versi terbaru)
- [Halaman rilis](https://github.com/hdzmxx/Bel-Sekolah/releases/latest) (catatan versi dan semua berkas)

Simpan `BelSekolah.exe` di folder tetap (mis. `C:\BelSekolah`) lalu jalankan.
Tidak perlu memasang Python. Untuk Windows 7 lihat bagian [Windows 7](#windows-7) di bawah.

## Fitur unggulan

**Presisi sampai hitungan detik**
Jam bel diatur dalam format jam:menit:detik, bukan hanya jam:menit. Bel berbunyi tepat pada detik yang
ditentukan, dan tidak berbunyi berulang-ulang dalam detik yang sama.

**Pilihan hari yang fleksibel**
Selain hari tunggal (Senin sampai Minggu), tersedia pilihan gabungan **Senin–Kamis**, **Senin–Jumat**, dan
**Senin–Sabtu**. Cocok untuk sekolah yang jam pulang hari Jumat-nya berbeda: cukup buat satu jadwal
Senin–Kamis dan satu jadwal Jumat, tanpa mengetik ulang per hari.

**Kategori jadwal yang bisa dipindah satu klik**
Simpan beberapa set jadwal sekaligus, misalnya *Reguler*, *Ujian*, atau *Ramadan*, lalu ganti jadwal aktif dari
dropdown di Beranda. Tidak perlu menghapus dan membuat ulang jadwal setiap kali kalender sekolah berubah.

**Tampilan yang langsung relevan**
- Halaman Jadwal otomatis menampilkan **jadwal hari ini** dan ikut berganti saat tengah malam.
- Beranda menampilkan jam besar, hitung mundur ke bel berikutnya, dan status tiap bel hari ini
  (Sudah / Berikutnya / Menunggu).
- Menambah banyak jadwal sekaligus dipermudah dengan opsi *Buat lagi setelah simpan* dan
  *Pertahankan data yang diisi*.

**Mudah dipindah ke komputer lain**
- **Ekspor / Impor** membungkus semua jadwal dan file nada ke satu berkas `.zip`.
- Saat impor, pilih **Ganti** (timpa semuanya) atau **Gabung** (tambahkan tanpa duplikat dan tanpa mengubah
  nama sekolah dan volume).
- **Mode portabel:** data tersimpan di folder `data/` dan `nada/` di sebelah aplikasi, jadi satu folder bisa
  disalin begitu saja.

**Bel yang tetap berbunyi**
- Mencegah komputer masuk mode tidur selama bel aktif.
- Bisa **jalan otomatis saat Windows menyala**, sehingga bel tetap hidup setelah komputer dihidupkan ulang.
- Pemutar suara punya **cadangan**: jika pemutar utama Windows gagal membuka sebuah mp3, aplikasi mencoba
  lewat Windows Media Player (PowerShell).

**Ringan dan mandiri**
- Satu berkas `.exe`, tanpa instalasi dan tanpa Python di komputer sekolah.
- Bekerja **sepenuhnya offline**, tanpa akun dan tanpa internet.
- Dapat dibuat untuk **Windows 7** (lihat bagian di bawah).
- Nada bawaan (Ding-dong dan Bel panjang) dibuat oleh aplikasi sendiri, atau pakai **mp3/wav** milik sekolah.
  Nada sendiri bisa dibungkus ke dalam exe.

## Fitur lainnya

- Pengaturan nama sekolah, alamat, dan volume (dengan tombol tes suara).
- Tombol **Coba bunyikan** untuk mendengar nada sebuah jadwal sebelum dipakai.
- Tombol **Hentikan suara** untuk menghentikan bel yang sedang berbunyi.
- Menu **Kumpulkan semua nada ke folder nada** untuk merapikan file nada yang tersebar.

## Menjalankan

Butuh Python 3.8 atau lebih baru (Tkinter sudah termasuk di Python untuk Windows).

```
python bel_sekolah.py
```

Di Linux/macOS pasang dulu `pygame` untuk suara dan Tkinter bila belum ada:

```
pip install -r requirements.txt
```

## Membuat .exe (Windows)

Jalankan `build.bat`, atau manual:

```
pip install pyinstaller==5.13.2
pyinstaller --noconsole --onefile --name BelSekolah bel_sekolah.py
```

Hasilnya ada di `dist/BelSekolah.exe`. Simpan di folder tetap (mis. `C:\BelSekolah`);
folder `data` dan `nada` akan dibuat di sebelahnya.

**Membungkus nada sendiri:** taruh file mp3/wav di folder `nada` (sejajar dengan `bel_sekolah.py`)
sebelum menjalankan `build.bat`. File-file itu ikut dibungkus ke dalam exe dan disalin ke folder
`nada` di sebelah exe saat pertama kali dijalankan. Folder `nada` tidak ikut ke GitHub
(lihat `.gitignore`), jadi pembuatan exe dilakukan di komputer yang punya file nadanya.

### Windows 7

Python 3.9 ke atas tidak mendukung Windows 7, jadi buat .exe dengan **Python 3.8.10**
(pilih 32-bit agar jalan di Windows 7 32-bit maupun 64-bit). Jika .exe gagal dibuka di Windows 7:

| Pesan error | Penyebab / solusi |
|---|---|
| `api-ms-win-crt-runtime-l1-1-0.dll is missing` | Pasang Service Pack 1, lalu update **KB4474419** dan **KB2999226** (Universal C Runtime). |
| `Error loading Python DLL ... python38.dll` | Runtime Windows belum lengkap (lihat di atas) atau bit-ness tidak cocok (exe 64-bit di Windows 32-bit). |
| `DLL load failed while importing _tkinter` | Pasang update **KB2533623**. |

Visual C++ Redistributable terbaru tidak bisa dipasang di Windows 7; gunakan update di atas.

## Data dan pencadangan

| Lokasi | Isi |
|---|---|
| `data/config.json` | Jadwal, kategori, nama sekolah, volume |
| `nada/` | File nada yang dipakai jadwal |

Gunakan menu **Berkas → Ekspor database dan nada…** secara berkala untuk membuat cadangan,
dan **Impor** untuk memulihkannya di komputer yang sama atau berbeda.

## Catatan

- Aplikasi harus tetap terbuka (boleh diminimalkan) agar bel berbunyi.
- Saat bel aktif, aplikasi mencegah komputer masuk mode tidur.

## Lisensi

[MIT](LICENSE) © 2026 HDZMXX
