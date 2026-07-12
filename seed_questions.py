"""
seed_questions.py — Bank soal interaktif Matematika Kelas 1 SD
Tipe soal:
  pilgan       — 4 pilihan (a/b/c/d)
  isian        — numpad angka
  hitung       — klik emoji satu per satu
  visual_pilgan— lihat deretan emoji, pilih angka
  jodohkan     — kotak emoji di kiri, pilih angka yang cocok di kanan
  hitung_warna — kotak emoji campur warna, hitung warna tertentu
  visual_tambah— A emoji + B emoji = ? (numpad)

Format:
  pilgan:       (kc, soal, a, b, c, d, 'a'-'d', diff, 'pilgan')
  isian:        (kc, soal, '','','','', angka, diff, 'isian')
  hitung:       (kc, soal, emoji, jumlah, '','', jumlah, diff, 'hitung')
  visual_pilgan:(kc, soal, emoji, jumlah, salah1, salah2, jumlah, diff, 'visual_pilgan')
  jodohkan:     (kc, soal, emoji, jumlah, salah1, salah2, jumlah, diff, 'jodohkan')
  hitung_warna: (kc, soal, 'e1 e2 e3...', target_emoji, '','', jumlah, diff, 'hitung_warna')
  visual_tambah:(kc, soal, emoji1, jumlah1, emoji2, jumlah2, total, diff, 'visual_tambah')

Layout soal: gunakan \\n\\n untuk pisahkan keterangan dan pertanyaan
"""

import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ".")
from database import init_db, insert_question, count_questions, get_conn

init_db()

Q = [

# ════════════════════════════════════════════════════════════════
# KC-B1: Mengenal bilangan 1–10
# ════════════════════════════════════════════════════════════════
("KC-B1","Angka ini dibaca apa?\n\n5","tiga","empat","lima","enam","c",1,"pilgan"),
("KC-B1","Angka ini dibaca apa?\n\n8","enam","tujuh","delapan","sembilan","c",1,"pilgan"),
("KC-B1","Angka ini dibaca apa?\n\n3","satu","dua","tiga","empat","c",1,"pilgan"),
("KC-B1","Bilangan manakah yang dibaca TUJUH?","5","6","7","8","c",1,"pilgan"),
("KC-B1","Bilangan manakah yang dibaca SEMBILAN?","7","8","9","10","c",1,"pilgan"),
("KC-B1","Angka EMPAT ditulis dengan angka...\n\nKetik jawabanmu!","","","","","4",1,"isian"),
("KC-B1","Angka ENAM ditulis dengan angka...\n\nKetik jawabanmu!","","","","","6",1,"isian"),

# ════════════════════════════════════════════════════════════════
# KC-B2: Membilang 1–10
# ════════════════════════════════════════════════════════════════  
# KC-B2: Membilang 1–10
("KC-B2","Klik setiap 🍎 satu per satu!\n\nAda berapa apel?","🍎","4","","","4",1,"hitung"),
("KC-B2","Klik setiap 🌸 satu per satu!\n\nAda berapa bunga?","🌸","6","","","6",1,"hitung"),
("KC-B2","Klik setiap ⭐ satu per satu!\n\nAda berapa bintang?","⭐","7","","","7",1,"hitung"),

# Tambahkan versi langsung input angka (lebih mudah untuk siswa)
("KC-B2","Ada berapa 🍎 di bawah ini?\n🍎 🍎 🍎 🍎","4","","","","4",1,"isian"),
("KC-B2","Ada berapa 🌸 di bawah ini?\n🌸 🌸 🌸 🌸 🌸 🌸","6","","","","6",1,"isian"),
# ════════════════════════════════════════════════════════════════
# KC-B3: Mengenal bilangan 11–20
# ════════════════════════════════════════════════════════════════
("KC-B3","Angka ini dibaca apa?\n\n14","tiga belas","empat belas","lima belas","enam belas","b",1,"pilgan"),
("KC-B3","Angka ini dibaca apa?\n\n17","enam belas","tujuh belas","delapan belas","sembilan belas","b",1,"pilgan"),
("KC-B3","Angka ini dibaca apa?\n\n20","delapan belas","sembilan belas","dua puluh","dua belas","c",1,"pilgan"),
("KC-B3","Angka ini dibaca apa?\n\n11","sepuluh","sebelas","dua belas","tiga belas","b",1,"pilgan"),
("KC-B3","DUA BELAS ditulis dengan angka...\n\nKetik jawabanmu!","","","","","12",1,"isian"),
("KC-B3","SEMBILAN BELAS ditulis dengan angka...\n\nKetik jawabanmu!","","","","","19",1,"isian"),

# ════════════════════════════════════════════════════════════════
# KC-B4: Membilang 11–20
# ════════════════════════════════════════════════════════════════
("KC-B4","Klik setiap 🌟 satu per satu!\n\nAda berapa bintang?","🌟","12","","","12",2,"hitung"),
("KC-B4","Klik setiap 🍊 satu per satu!\n\nAda berapa jeruk?","🍊","15","","","15",2,"hitung"),
("KC-B4","Lihat hatinya!\n\nAda berapa ❤️?","❤️","13","11","16","13",2,"visual_pilgan"),
("KC-B4","Di keranjang ada 10 telur 🥚.\nIbu menaruh 5 telur lagi.\n\nAda berapa telur sekarang?","13","14","15","16","c",2,"pilgan"),
("KC-B4","Hitung: 10 + 7 = ?\n\nKetik jawabanmu!","","","","","17",2,"isian"),

# ════════════════════════════════════════════════════════════════
# KC-B5: Membandingkan dua bilangan
# ════════════════════════════════════════════════════════════════
("KC-B5","Siti punya 7 permen 🍬.\nAni punya 5 permen 🍬.\n\nSiapa yang punya lebih banyak?","Ani","Siti","sama banyak","tidak tahu","b",1,"pilgan"),
("KC-B5","Bandingkan dua bilangan ini:\n\nMana yang lebih besar, 9 atau 6?","6","9","sama besar","tidak tahu","b",1,"pilgan"),
("KC-B5","Bandingkan dua bilangan ini:\n\nMana yang lebih kecil, 4 atau 8?","8","4","sama kecil","tidak tahu","b",1,"pilgan"),
("KC-B5","Di kelas ada 12 anak laki-laki 🧒\ndan 15 anak perempuan 👧.\n\nMana yang lebih banyak?","anak laki-laki","sama banyak","anak perempuan","tidak tahu","c",2,"pilgan"),
("KC-B5","Bandingkan dua bilangan ini:\n\nMana yang lebih kecil, 11 atau 15?","15","sama kecil","11","tidak tahu","c",2,"pilgan"),
("KC-B5","Bandingkan dua bilangan ini:\n\nMana yang lebih besar, 7 atau 3?","3","7","sama besar","tidak tahu","b",1,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-B6: Urutan bilangan
# ════════════════════════════════════════════════════════════════
("KC-B6","Perhatikan urutan angka berikut:\n1, 2, 3, 4, 5, 6, ?\n\nAngka setelah 6 adalah?","5","7","8","9","b",1,"pilgan"),
("KC-B6","Perhatikan urutan angka berikut:\n?, 8, 9, 10\n\nAngka sebelum 8 adalah?","7","6","5","4","a",1,"pilgan"),
("KC-B6","Angka yang ada di antara 5 dan 7\n\nKetik jawabanmu!","","","","","6",1,"isian"),
("KC-B6","Angka setelah 15\n\nKetik jawabanmu!","","","","","16",1,"isian"),
("KC-B6","Urutkan dari kecil ke besar:\n5, 2, 8, 1\n\nUrutan yang benar adalah...","1 2 5 8","8 5 2 1","5 2 8 1","2 5 1 8","a",1,"pilgan"),
("KC-B6","Angka yang ada di antara 12 dan 14\n\nKetik jawabanmu!","","","","","13",2,"isian"),

# ════════════════════════════════════════════════════════════════
# KC-B7: Nilai tempat satuan
# ════════════════════════════════════════════════════════════════
("KC-B7","Perhatikan angka berikut:\n\n13\n\nAngka 3 ada di tempat...","puluhan","satuan","ratusan","ribuan","b",2,"pilgan"),
("KC-B7","Perhatikan angka berikut:\n\n18\n\nAngka 8 ada di tempat...","puluhan","ratusan","satuan","ribuan","c",2,"pilgan"),
("KC-B7","Perhatikan angka berikut:\n16 = 1 puluhan + ? satuan\n\nBerapa satuannya?","4","5","6","7","c",2,"pilgan"),
("KC-B7","Perhatikan angka berikut:\n\n15\n\nBerapa angka di tempat satuan?\n\nKetik jawabanmu!","","","","","5",2,"isian"),
("KC-B7","Perhatikan angka berikut:\n\n19\n\nBerapa angka di tempat satuan?\n\nKetik jawabanmu!","","","","","9",2,"isian"),
("KC-B7","Perhatikan angka berikut:\n\n20\n\nAngka 0 ada di tempat...","satuan","puluhan","ratusan","ribuan","a",2,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-B8: Nilai tempat puluhan
# ════════════════════════════════════════════════════════════════
("KC-B8","Perhatikan angka berikut:\n\n17\n\nAngka 1 ada di tempat...","satuan","puluhan","ratusan","ribuan","b",2,"pilgan"),
("KC-B8","Perhatikan angka berikut:\n\n20\n\nAngka 2 ada di tempat...","satuan","puluhan","ratusan","ribuan","b",2,"pilgan"),
("KC-B8","1 puluhan + 5 satuan = ?\n\nKetik jawabanmu!","","","","","15",2,"isian"),
("KC-B8","1 puluhan + 3 satuan = ?\n\nKetik jawabanmu!","","","","","13",2,"isian"),
("KC-B8","1 puluhan + 7 satuan = ?\n\nKetik jawabanmu!","","","","","17",2,"isian"),
("KC-B8","1 puluhan + 9 satuan = angka...","91","19","9","10","b",2,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-O1: Konsep penjumlahan
# ════════════════════════════════════════════════════════════════
("KC-O1","Dito punya 2 kue 🎂.\nIbu memberi 1 kue lagi.\n\nSekarang Dito punya berapa kue?","2","3","4","1","b",1,"pilgan"),
("KC-O1","Ada 3 anak laki-laki 🧒\ndan 2 anak perempuan 👧.\n\nAda berapa anak semuanya?","3","4","5","6","c",1,"pilgan"),
("KC-O1","Tanda ➕ dalam matematika artinya...","kurang","tambah","bagi","sama dengan","b",1,"pilgan"),
("KC-O1","0 + 6 = ?\n\nKetik jawabanmu!","","","","","6",1,"isian"),
# visual_tambah: lihat emoji lalu jumlahkan
("KC-O1","Hitung semuanya!\n\nBerapa jumlah apel dan jeruk?","🍎","2","🍊","1","3",1,"visual_tambah"),
("KC-O1","Penjumlahan artinya kita menggabungkan dua kelompok.\n\nManakah contoh penjumlahan?","8 - 3","5 + 2","9 > 4","7 < 10","b",1,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-O2: Penjumlahan hasil sampai 10
# ════════════════════════════════════════════════════════════════
# visual_tambah
("KC-O2","Hitung semuanya!\n\nBerapa jumlah ikan?","🐟","3","🐟","4","7",1,"visual_tambah"),
("KC-O2","Hitung semuanya!\n\nBerapa jumlah buah?","🍎","4","🍊","3","7",1,"visual_tambah"),
# jodohkan
("KC-O2","Cocokkan kelompok bintang dengan angka yang tepat!\n\nAda berapa ⭐?","⭐","6","4","9","6",1,"jodohkan"),
("KC-O2","3 + 4 = ?\n\nKetik jawabanmu!","","","","","7",1,"isian"),
("KC-O2","5 + 5 = ?\n\nKetik jawabanmu!","","","","","10",1,"isian"),
("KC-O2","2 + 7 = ?\n\nKetik jawabanmu!","","","","","9",1,"isian"),
("KC-O2","4 + 4 = ?","6","7","8","9","c",1,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-O3: Penjumlahan hasil sampai 20
# ════════════════════════════════════════════════════════════════
("KC-O3","9 + 5 = ?\n\nKetik jawabanmu!","","","","","14",2,"isian"),
("KC-O3","8 + 7 = ?\n\nKetik jawabanmu!","","","","","15",2,"isian"),
("KC-O3","10 + 7 = ?\n\nKetik jawabanmu!","","","","","17",2,"isian"),
("KC-O3","7 + 8 = ?\n\nKetik jawabanmu!","","","","","15",2,"isian"),
("KC-O3","Hitung semuanya!\n\nBerapa jumlah telur?","🥚","9","🥚","6","15",2,"visual_tambah"),
("KC-O3","Ada 9 siswa 🧑 di kelas A\ndan 8 siswa di kelas B.\n\nAda berapa siswa semuanya?","15","16","17","18","c",2,"pilgan"),
("KC-O3","9 + 9 = ?","16","17","18","19","c",2,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-O4: Konsep pengurangan
# ════════════════════════════════════════════════════════════════
("KC-O4","Ada 5 kue 🎂 di piring.\nDimakan 2 kue.\n\nSisa berapa kue?","2","3","4","5","b",1,"pilgan"),
("KC-O4","Rani punya 6 balon 🎈.\n1 balon meletus 💥.\n\nSisa berapa balon?","4","5","6","7","b",1,"pilgan"),
("KC-O4","Tanda ➖ dalam matematika artinya...","tambah","kurang","kali","bagi","b",1,"pilgan"),
("KC-O4","5 - 5 = ?\n\nKetik jawabanmu!","","","","","0",1,"isian"),
("KC-O4","8 - 0 = ?\n\nKetik jawabanmu!","","","","","8",1,"isian"),
("KC-O4","Pengurangan artinya kita...","menggabungkan","menambah","mengambil sebagian","melipatkan","c",1,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-O5: Pengurangan dari bilangan sampai 10
# ════════════════════════════════════════════════════════════════
("KC-O5","Klik setiap 🦋!\nAda 10 kupu-kupu, 3 terbang pergi.\n\nKlik kupu-kupu yang tersisa!","🦋","7","","","7",1,"hitung"),
("KC-O5","8 - 3 = ?\n\nKetik jawabanmu!","","","","","5",1,"isian"),
("KC-O5","10 - 6 = ?\n\nKetik jawabanmu!","","","","","4",1,"isian"),
("KC-O5","9 - 4 = ?","4","5","6","7","b",1,"pilgan"),
("KC-O5","Ada 8 permen 🍬.\nDimakan 5.\n\nSisa berapa?","2","3","4","5","b",1,"pilgan"),
("KC-O5","6 - 2 = ?\n\nKetik jawabanmu!","","","","","4",1,"isian"),
("KC-O5","10 - 3 = ?","5","6","7","8","c",1,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-O6: Pengurangan dari bilangan sampai 20
# ════════════════════════════════════════════════════════════════
("KC-O6","15 - 7 = ?\n\nKetik jawabanmu!","","","","","8",2,"isian"),
("KC-O6","18 - 9 = ?\n\nKetik jawabanmu!","","","","","9",2,"isian"),
("KC-O6","17 - 8 = ?","7","8","9","10","c",2,"pilgan"),
("KC-O6","20 - 6 = ?\n\nKetik jawabanmu!","","","","","14",2,"isian"),
("KC-O6","Lani siapkan 15 balon 🎈.\n6 balon meletus.\n\nSisa berapa balon?","7","8","9","10","c",2,"pilgan"),
("KC-O6","Ada 14 kue 🍪.\nDimakan 5.\n\nSisa berapa kue?","7","8","9","10","c",2,"pilgan"),
("KC-O6","16 - 7 = ?\n\nKetik jawabanmu!","","","","","9",2,"isian"),

# ════════════════════════════════════════════════════════════════
# KC-O7: Hubungan penjumlahan dan pengurangan
# ════════════════════════════════════════════════════════════════
("KC-O7","Perhatikan:\n4 + 5 = 9\n\nBerarti 9 - 5 = ?","3","4","5","6","b",3,"pilgan"),
("KC-O7","Perhatikan:\n6 + 7 = 13\n\nBerarti 13 - 7 = ?","5","6","7","8","b",3,"pilgan"),
("KC-O7","Ada 8 apel 🍎.\nDiambil beberapa.\nSisa 3 apel.\n\nBerapa apel yang diambil?\n\nKetik jawabanmu!","","","","","5",3,"isian"),
("KC-O7","3 + ? = 10\n\nAngka yang hilang?\n\nKetik jawabanmu!","","","","","7",3,"isian"),
("KC-O7","Perhatikan:\n9 + 8 = 17\n\nBerarti 17 - 8 = ?","7","8","9","10","c",3,"pilgan"),
("KC-O7","12 - ? = 5\n\nAngka yang hilang?\n\nKetik jawabanmu!","","","","","7",3,"isian"),

# ════════════════════════════════════════════════════════════════
# KC-G1: Mengenal bangun datar
# ════════════════════════════════════════════════════════════════
("KC-G1","Perhatikan benda berikut:\nRoda sepeda 🚲\n\nBentuknya adalah...","segitiga","persegi","lingkaran","persegi panjang","c",1,"pilgan"),
("KC-G1","Perhatikan benda berikut:\nBuku tulis 📚\n\nBentuknya adalah...","lingkaran","segitiga","persegi panjang","bintang","c",1,"pilgan"),
("KC-G1","Perhatikan benda berikut:\nUang koin 🪙\n\nBentuknya adalah...","segitiga","persegi","lingkaran","persegi panjang","c",1,"pilgan"),
("KC-G1","Perhatikan benda berikut:\nPapan tulis di kelas 🏫\n\nBentuknya adalah...","lingkaran","segitiga","persegi","persegi panjang","d",1,"pilgan"),
("KC-G1","Perhatikan benda berikut:\nPotongan pizza 🍕\n\nBentuknya adalah...","persegi","lingkaran","segitiga","persegi panjang","c",1,"pilgan"),
("KC-G1","Perhatikan benda berikut:\nSaputangan 🧣\n\nBentuknya adalah...","lingkaran","segitiga","persegi","persegi panjang","c",1,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-G2: Sifat bangun datar
# ════════════════════════════════════════════════════════════════
("KC-G2","Perhatikan bangun ini:\nSegitiga 🔺\n\nPunya berapa sisi?","2","3","4","5","b",2,"pilgan"),
("KC-G2","Perhatikan bangun ini:\nPersegi ⬛\n\nPunya berapa sudut?\n\nKetik jawabanmu!","","","","","4",2,"isian"),
("KC-G2","Perhatikan bangun ini:\nLingkaran ⭕\n\nPunya berapa sudut?","1","2","4","tidak ada","d",2,"pilgan"),
("KC-G2","Perhatikan bangun ini:\nPersegi panjang 🟥\n\nPunya berapa sisi?\n\nKetik jawabanmu!","","","","","4",2,"isian"),
("KC-G2","Bangun datar yang tidak punya sudut adalah...","persegi ⬛","segitiga 🔺","lingkaran ⭕","persegi panjang 🟥","c",2,"pilgan"),
("KC-G2","Perhatikan bangun ini:\nSegitiga 🔺\n\nPunya berapa sudut?\n\nKetik jawabanmu!","","","","","3",2,"isian"),

# ════════════════════════════════════════════════════════════════
# KC-G3: Mengelompokkan bangun datar
# ════════════════════════════════════════════════════════════════
("KC-G3","Uang koin 🪙, roda 🔵, jam dinding 🕐\n\nSemuanya berbentuk...","segitiga","persegi","lingkaran","persegi panjang","c",2,"pilgan"),
("KC-G3","Buku 📚, papan tulis, dan pintu\n\nSemuanya berbentuk...","lingkaran","segitiga","persegi panjang","bintang","c",2,"pilgan"),
("KC-G3","🪙 uang koin, 🔵 roda, 📚 buku, 🕐 jam\n\nMana yang bentuknya BERBEDA dari yang lain?","uang koin","roda","buku","jam","c",2,"pilgan"),
("KC-G3","Segitiga 🔺 dan persegi ⬛\n\nKedua bangun ini sama-sama punya...","tidak ada sudut","sudut","bentuk bulat","tidak ada sisi","b",2,"pilgan"),
("KC-G3","Manakah yang berbentuk lingkaran?\n","penggaris 📏","buku 📚","piring 🍽️","pintu 🚪","c",2,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-P1: Perbandingan panjang (GANTI soal ambigu → pakai angka)
# ════════════════════════════════════════════════════════════════
("KC-P1","Tali merah panjangnya 8 cm.\nTali biru panjangnya 5 cm.\n\nMana yang lebih panjang?","tali biru","sama panjang","tali merah","tidak bisa dibanding","c",1,"pilgan"),
("KC-P1","Tongkat A panjangnya 10 cm.\nTongkat B panjangnya 6 cm.\n\nMana yang lebih pendek?","tongkat A","sama panjang","tongkat B","tidak bisa dibanding","c",1,"pilgan"),
("KC-P1","Gajah 🐘 tingginya 3 meter.\nKucing 🐱 tingginya 30 cm.\n\nMana yang lebih tinggi?","kucing","sama tinggi","gajah","tidak tahu","c",1,"pilgan"),
("KC-P1","Lawan kata PANJANG adalah...","besar","tebal","pendek","tinggi","c",1,"pilgan"),
("KC-P1","Jalan raya 🛣️ panjangnya 2 km.\nGang kecil panjangnya 20 meter.\n\nMana yang lebih panjang?","gang kecil","sama panjang","jalan raya","tidak tahu","c",1,"pilgan"),
("KC-P1","Tali A lebih pendek dari tali B.\n\nBerarti tali B lebih ... dari tali A","pendek","sama","panjang","tidak bisa dibanding","c",1,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-P2: Perbandingan berat (GANTI soal ambigu → pakai angka)
# ════════════════════════════════════════════════════════════════
("KC-P2","Buku beratnya 500 gram.\nPensil beratnya 10 gram.\n\nMana yang lebih berat?","pensil","sama berat","buku","tidak tahu","c",1,"pilgan"),
("KC-P2","Gajah 🐘 beratnya 5000 kg.\nKelinci 🐰 beratnya 2 kg.\n\nMana yang lebih berat?","kelinci","sama berat","gajah","tidak tahu","c",1,"pilgan"),
("KC-P2","Lawan kata BERAT adalah...","kecil","tipis","ringan","pendek","c",1,"pilgan"),
("KC-P2","Semangka 🍉 beratnya 3 kg.\nAnggur 🍇 beratnya 500 gram.\n\nMana yang lebih berat?","anggur","semangka","sama berat","tidak tahu","b",1,"pilgan"),
("KC-P2","Tas berisi 5 buku beratnya 2 kg.\nTas kosong beratnya 200 gram.\n\nMana yang lebih berat?","tas kosong","sama berat","tas berisi buku","tidak tahu","c",1,"pilgan"),
("KC-P2","Batu besar 🪨 beratnya 10 kg.\nBulu ayam 🪶 beratnya 5 gram.\n\nMana yang lebih berat?","bulu","sama berat","batu","tidak tahu","c",1,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-P3: Urutan kejadian dan waktu
# ════════════════════════════════════════════════════════════════
("KC-P3","Kegiatan di PAGI hari sebelum sekolah:\n\nKegiatan mana yang dilakukan pertama?","tidur malam","makan malam","bangun tidur dan mandi","nonton TV malam","c",1,"pilgan"),
("KC-P3","Urutan kegiatan pagi yang benar:\n\nManakah urutan yang tepat?","tidur → bangun → makan siang","bangun → mandi → sarapan → sekolah","sekolah → bangun → mandi","makan malam → sekolah → tidur","b",1,"pilgan"),
("KC-P3","Kegiatan di MALAM hari setelah belajar:\n\nKegiatan apa yang dilakukan?","sarapan","berangkat sekolah","bermain siang","tidur","d",1,"pilgan"),
("KC-P3","Sebelum berangkat ke sekolah 🏫,\nkita biasanya...\n\nApa yang dilakukan lebih dulu?","makan malam","tidur siang","sarapan pagi","bermain malam","c",1,"pilgan"),
("KC-P3","Hari ini Selasa 📅.\n\nBesok adalah hari?","Senin","Selasa","Rabu","Kamis","c",1,"pilgan"),
("KC-P3","Hari ini Jumat 📅.\n\nKemarin adalah hari?","Kamis","Jumat","Sabtu","Rabu","a",1,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-A1: Mengenal pola berulang
# ════════════════════════════════════════════════════════════════
("KC-A1","Perhatikan pola warna:\n🔴🔵🔴🔵🔴🔵\n\nBagian yang diulang adalah...","🔴🔴","🔵🔵","🔴🔵","🔵🔴","c",1,"pilgan"),
("KC-A1","Perhatikan pola bintang:\n⭐🌙⭐🌙⭐🌙\n\nIni adalah pola...","AAAA","ABAB","AABB","ABBA","b",1,"pilgan"),
("KC-A1","Perhatikan pola hewan:\n🐱🐶🐱🐶🐱🐶\n\nSatu bagian pola ada berapa gambar?","1","2","3","4","b",1,"pilgan"),
("KC-A1","Manakah yang merupakan pola berulang?\n","1 2 3 4 5","🔴🔵🔴🔵🔴🔵","A B C D E","semua berbeda","b",1,"pilgan"),
("KC-A1","Perhatikan pola warna:\n🟡🟢🟣🟡🟢🟣\n\nAda berapa warna dalam satu unit pola?","1","2","3","4","c",1,"pilgan"),
("KC-A1","Ketukan gendang:\nduk - tak - duk - tak - duk - tak 🥁\n\nBagian yang diulang adalah...","duk saja","tak saja","duk-tak","tidak ada","c",1,"pilgan"),

# ════════════════════════════════════════════════════════════════
# KC-A2: Melanjutkan pola
# ════════════════════════════════════════════════════════════════
("KC-A2","Perhatikan pola:\n🔴🔵🔴🔵🔴 ___\n\nApa yang selanjutnya?","🔴","🔵","🟡","🟢","b",1,"pilgan"),
("KC-A2","Perhatikan pola:\n⭐🌙⭐🌙⭐ ___\n\nApa yang selanjutnya?","⭐","🌙","☀️","🌟","b",1,"pilgan"),
("KC-A2","Perhatikan pola:\n🟡🟢🟣🟡🟢 ___\n\nApa yang selanjutnya?","🟡","🟢","🟣","🔵","c",1,"pilgan"),
("KC-A2","Perhatikan pola angka:\n1 2 1 2 1 ___\n\nAngka selanjutnya?","1","2","3","4","b",1,"pilgan"),
("KC-A2","Perhatikan pola:\n🐱🐱🐶🐱🐱🐶🐱🐱 ___\n\nApa yang selanjutnya?","🐱","🐶","🐰","🐷","b",1,"pilgan"),
("KC-A2","Perhatikan pola:\nbesar - kecil - besar - kecil - besar ___\n\nApa yang selanjutnya?","besar","kecil","sedang","sangat besar","b",1,"pilgan"),

# ════════════════════════════════════════════════════════════════
# Contoh hitung_warna (kotak bola warna-warni)
# Format: emoji_string (spasi-separated), target_emoji, answer
# ════════════════════════════════════════════════════════════════
("KC-B2","Perhatikan kotak bola berikut!\n\nAda berapa bola MERAH 🔴?",
 "🔴 🔵 🔴 🟡 🔴 🔵 🟡 🔴","🔴","","","4",1,"hitung_warna"),
("KC-B2","Perhatikan kotak bola berikut!\n\nAda berapa bola BIRU 🔵?",
 "🔴 🔵 🔴 🟡 🔵 🔵 🟡 🔴","🔵","","","3",1,"hitung_warna"),
("KC-O2","Perhatikan kotak buah berikut!\n\nAda berapa 🍎 apel?",
 "🍎 🍊 🍎 🍋 🍎 🍊 🍎 🍋 🍎","🍎","","","5",1,"hitung_warna"),
("KC-O2","Perhatikan kotak buah berikut!\n\nAda berapa 🍊 jeruk?",
 "🍎 🍊 🍋 🍊 🍎 🍊 🍋 🍎","🍊","","","3",1,"hitung_warna"),
("KC-O5","Perhatikan kotak bintang berikut!\n\nAda berapa bintang KUNING ⭐?",
 "⭐ 🌟 ⭐ 💫 ⭐ 🌟 ⭐ 💫 ⭐","⭐","","","5",1,"hitung_warna"),

# ════════════════════════════════════════════════════════════════
# Contoh jodohkan (matching)
# ════════════════════════════════════════════════════════════════
("KC-B2","Cocokkan! Berapa banyak bintang di kotak?\n\nPilih angka yang tepat!","⭐","5","3","8","5",1,"jodohkan"),
("KC-B2","Cocokkan! Berapa banyak bunga di kotak?\n\nPilih angka yang tepat!","🌸","4","2","7","4",1,"jodohkan"),
("KC-B3","Cocokkan! Berapa banyak bintang di kotak?\n\nPilih angka yang tepat!","⭐","12","9","15","12",2,"jodohkan"),
("KC-O2","Cocokkan! Berapa banyak apel di kotak?\n\nPilih angka yang tepat!","🍎","8","5","10","8",1,"jodohkan"),
("KC-O3","Cocokkan! Berapa banyak balon di kotak?\n\nPilih angka yang tepat!","🎈","14","11","17","14",2,"jodohkan"),
]


def seed():
    if count_questions() > 0:
        print(f"Soal sudah ada ({count_questions()} soal). Gunakan --force untuk reset.")
        return
    for q in Q:
        insert_question(*q)
    total = count_questions()
    print(f"Selesai: {total} soal.\n")
    with get_conn() as conn:
        rows  = conn.execute("SELECT kc_id, COUNT(*) as n FROM questions GROUP BY kc_id ORDER BY kc_id").fetchall()
        rows2 = conn.execute("SELECT question_type, COUNT(*) as n FROM questions GROUP BY question_type").fetchall()
    for r in rows: print(f"  {r['kc_id']}: {r['n']} soal")
    print("\nPer tipe:")
    for r in rows2: print(f"  {r['question_type']}: {r['n']} soal")


if __name__ == "__main__":
    import sys as _sys
    if "--force" in _sys.argv:
        with get_conn() as conn:
            conn.execute("DELETE FROM questions")
        print("Bank soal dikosongkan.\n")
    seed()
