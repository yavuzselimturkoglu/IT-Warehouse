#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAID Hesaplayıcı – modern ttk görünüm + tür bazlı kısa açıklamalar
Destek: RAID 0, 1, 1E, 5, 5E, 5EE, 6, 10, 50, 60
"""

import tkinter as tk
from tkinter import ttk, messagebox

APP_TITLE = "RAID-CALCULATOR"

RAID_TYPES = [
    "RAID 0 (Stripe set)",
    "RAID 1 (Mirror)",
    "RAID 1E (Striped mirrors; odd disk sayısı destekler)",
    "RAID 5 (Parity)",
    "RAID 5E (Parity + dedicated hot spare)",
    "RAID 5EE (Parity + distributed spare)",
    "RAID 6 (Double parity)",
    "RAID 10 (Mirror + stripe)",
    "RAID 50 (RAID 5 + 0)",
    "RAID 60 (RAID 6 + 0)",
]

# Sağ panelde gösterilecek, kısa ve “çok derine inmeyen” açıklamalar
RAID_BRIEFS = {
    "RAID 0":  "Veriyi tüm disklere paralel yazar/okur. Kapasite tüm disklerin toplamıdır, performans yüksektir fakat hata toleransı yoktur.",
    "RAID 1":  "Disklerin ayna kopyasıdır. Kapasite tek disk kadardır. Okuma paralelleşir; bir disk bozulsa bile veri çalışır.",
    "RAID 1E": "Aynalı şerit yapısıdır; tek/çift sayıda diskle çalışır. Kapasite toplamın yarısıdır. Hata toleransı topolojiye bağlıdır.",
    "RAID 5":  "Tek parite kullanır. Kapasite (N-1) disk kadardır. Bir disk kaybına dayanır; yazma parite nedeniyle daha maliyetlidir.",
    "RAID 5E": "RAID 5 + ayrılmış sıcak yedek (hot spare). Kapasite (N-2) disk kadardır. Bir disk kaybında yedek otomatik devreye girer.",
    "RAID 5EE":"RAID 5 + dağıtık sıcak yedek. Kapasite (N-2) disk kadardır. Yedek alanı tüm disklere dağıtıldığı için yeniden kurulum hızlıdır.",
    "RAID 6":  "Çift parite. Kapasite (N-2) disk kadardır. İki disk kaybına dayanır; yazma maliyeti RAID 5'ten yüksektir.",
    "RAID 10": "Aynalı çiftlerin üzerine şerit atılır. Kapasite toplamın yarısıdır. Okuma çok hızlı; hata toleransı çift dağılımına bağlıdır.",
    "RAID 50": "Birden çok RAID 5 grubunun üzerine şerit. Her grup 1 disk kaybına dayanır; kapasite grup başına (k-1) disktir.",
    "RAID 60": "Birden çok RAID 6 grubunun üzerine şerit. Her grup 2 disk kaybına dayanır; kapasite grup başına (k-2) disktir.",
}

def human_tb(value: float) -> str:
    s = f"{value:.2f}"
    if s.endswith("00"): s = s[:-3]
    elif s.endswith("0"): s = s[:-1]
    return s

def choose_groups(n: int, min_group_size: int):
    # Eşit grupları tercih eden basit yerleşim
    if n % 2 == 0 and (n // 2) >= min_group_size:
        return 2, n // 2
    if n % 3 == 0 and (n // 3) >= min_group_size:
        return 3, n // 3
    g = max(2, n // max(min_group_size, 1))
    while g > 1:
        if n % g == 0 and (n // g) >= min_group_size:
            return g, n // g
        g -= 1
    return 1, n

def calc_raid(n: int, size_tb: float, raid_label: str):
    """(capacity_tb, speed_text, fault_text, warn_text, layout_text)"""
    warn = None
    layout = ""

    if raid_label.startswith("RAID 0"):
        if n < 2: raise ValueError("RAID 0 için en az 2 disk gerekir.")
        capacity = n * size_tb
        speed = f"Okuma/Yazma ~ {n}×"
        fault = "0"

    elif raid_label.startswith("RAID 1 ("):
        if n < 2: raise ValueError("RAID 1 için en az 2 disk gerekir.")
        capacity = 1 * size_tb
        speed = f"Okuma ~ {n}×; Yazma ~ 1×"
        fault = f"{n-1}"

    elif raid_label.startswith("RAID 1E"):
        if n < 3: raise ValueError("RAID 1E için en az 3 disk gerekir.")
        capacity = (n * size_tb) / 2.0
        speed = f"Okuma ~ {n}×; Yazma ~ {max(1, n//2)}×"
        fault = "Topolojiye bağlı (genelde ≥1)."

    elif raid_label.startswith("RAID 5E"):
        if n < 4: raise ValueError("RAID 5E için en az 4 disk gerekir.")
        capacity = (n - 2) * size_tb
        speed = f"Okuma ~ {n-1}×; Yazma parite maliyetli"
        fault = "1 (hot spare devreye girer)."

    elif raid_label.startswith("RAID 5EE"):
        if n < 4: raise ValueError("RAID 5EE için en az 4 disk gerekir.")
        capacity = (n - 2) * size_tb
        speed = f"Okuma ~ {n-1}×; Yazma parite maliyetli"
        fault = "1 (dağıtık yedek)."

    elif raid_label.startswith("RAID 5"):
        if n < 3: raise ValueError("RAID 5 için en az 3 disk gerekir.")
        capacity = (n - 1) * size_tb
        speed = f"Okuma ~ {n-1}×; Yazma parite maliyetli (~{max(1, n//2)}× eşdeğer)"
        fault = "1"

    elif raid_label.startswith("RAID 6") and " + 0" not in raid_label:
        if n < 4: raise ValueError("RAID 6 için en az 4 disk gerekir.")
        capacity = (n - 2) * size_tb
        speed = f"Okuma ~ {n-2}×; Yazma daha maliyetli"
        fault = "2"

    elif raid_label.startswith("RAID 10"):
        if n < 4 or n % 2 != 0:
            raise ValueError("RAID 10 için çift sayıda ve en az 4 disk gerekir.")
        capacity = (n / 2) * size_tb
        speed = f"Okuma ~ {n}×; Yazma ~ {n//2}×"
        fault = (f"Duruma bağlı (her ayna çiftinden en fazla 1). "
                 f"En kötü: 1, en iyi: {n//2}")
        warn = "Aynı ayna çiftindeki iki kayıp veri kaybına yol açar."

    elif raid_label.startswith("RAID 50"):
        if n < 6: raise ValueError("RAID 50 için en az 6 disk gerekir.")
        groups, k = choose_groups(n, 3)
        if groups < 2: raise ValueError("En az 2 grup ve grup başına ≥3 disk gerekir.")
        capacity = groups * (k - 1) * size_tb
        speed = f"Okuma ~ {groups*(k-1)}×; Yazma parite + şeride bağlı"
        fault = f"Her grupta 1 disk. En kötü: 1, en iyi: {groups}."
        layout = f"Yerleşim: {groups}×RAID5 (grup başına {k} disk)."

    elif raid_label.startswith("RAID 60"):
        if n < 8: raise ValueError("RAID 60 için en az 8 disk gerekir.")
        groups, k = choose_groups(n, 4)
        if groups < 2: raise ValueError("En az 2 grup ve grup başına ≥4 disk gerekir.")
        capacity = groups * (k - 2) * size_tb
        speed = f"Okuma ~ {groups*(k-2)}×; Yazma RAID6 maliyetli"
        fault = f"Her grupta 2 disk. En kötü: 2, en iyi: {2*groups}."
        layout = f"Yerleşim: {groups}×RAID6 (grup başına {k} disk)."

    else:
        raise ValueError("Bilinmeyen RAID türü.")

    return capacity, speed, fault, warn, layout

# --------- Arayüz ---------
class RaidApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("820x560")
        self.minsize(800, 540)
        self.configure(padx=18, pady=18, bg="#f5f7fb")

        # Modernimsi ttk stilleri
        self.style = ttk.Style(self)
        try: self.style.theme_use("clam")
        except: pass
        self.style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), background="#f5f7fb")
        self.style.configure("H3.TLabel", font=("Segoe UI", 12, "bold"), background="#f5f7fb")
        self.style.configure("Body.TLabel", font=("Segoe UI", 10), background="#f5f7fb", foreground="#222")
        self.style.configure("Muted.TLabel", font=("Segoe UI", 9), background="#f5f7fb", foreground="#555")
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        self.style.configure("Card.TFrame", background="#ffffff", relief="flat")
        self.style.map("Accent.TButton",
                       background=[("!disabled", "#4a6fff"), ("pressed", "#3450c8"), ("active", "#5678ff")],
                       foreground=[("!disabled", "#ffffff")])

        # Başlık
        ttk.Label(self, text="RAID parametrelerini girin", style="Title.TLabel")\
            .grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,10))

        # Sol: Form + Sonuçlar (iki kart)
        left = ttk.Frame(self, style="Card.TFrame")
        left.grid(row=1, column=0, sticky="nsew", padx=(0,12))
        left.configure(padding=16)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Form kartı
        ttk.Label(left, text="Girdi", style="H3.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,8))
        ttk.Label(left, text="Disk sayısı", style="Body.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        self.ent_disks = ttk.Entry(left, width=22)
        self.ent_disks.grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(left, text="Tek disk boyutu (TB)", style="Body.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        self.ent_size = ttk.Entry(left, width=22)
        self.ent_size.grid(row=2, column=1, sticky="w", pady=6)

        ttk.Label(left, text="RAID türü", style="Body.TLabel").grid(row=3, column=0, sticky="w", pady=6)
        self.cmb_raid = ttk.Combobox(left, values=RAID_TYPES, state="readonly", width=44)
        self.cmb_raid.current(0)
        self.cmb_raid.grid(row=3, column=1, sticky="w", pady=6)
        self.cmb_raid.bind("<<ComboboxSelected>>", self.on_raid_change)

        ttk.Button(left, text="Hesapla", style="Accent.TButton", command=self.on_calc)\
            .grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 4))

        ttk.Separator(left, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

        # Sonuç kartı
        ttk.Label(left, text="Sonuçlar", style="H3.TLabel").grid(row=6, column=0, columnspan=2, sticky="w", pady=(0,8))
        ttk.Label(left, text="Kapasite", style="Body.TLabel").grid(row=7, column=0, sticky="w", pady=6)
        self.lbl_capacity = ttk.Label(left, text="N/A", style="Body.TLabel")
        self.lbl_capacity.grid(row=7, column=1, sticky="w", pady=6)

        ttk.Label(left, text="Hız kazancı", style="Body.TLabel").grid(row=8, column=0, sticky="w", pady=6)
        self.lbl_speed = ttk.Label(left, text="N/A", style="Body.TLabel", wraplength=430, justify="left")
        self.lbl_speed.grid(row=8, column=1, sticky="w", pady=6)

        ttk.Label(left, text="Hata toleransı", style="Body.TLabel").grid(row=9, column=0, sticky="w", pady=6)
        self.lbl_fault = ttk.Label(left, text="N/A", style="Body.TLabel", wraplength=430, justify="left")
        self.lbl_fault.grid(row=9, column=1, sticky="w", pady=6)

        self.lbl_layout = ttk.Label(left, text="", style="Muted.TLabel", wraplength=520, justify="left")
        self.lbl_layout.grid(row=10, column=0, columnspan=2, sticky="w", pady=(4,0))

        self.lbl_warn = ttk.Label(left, text="", style="Muted.TLabel", wraplength=520, justify="left")
        self.lbl_warn.grid(row=11, column=0, columnspan=2, sticky="w", pady=(4,0))

        # Sağ: Bilgi kartı
        right = ttk.Frame(self, style="Card.TFrame")
        right.grid(row=1, column=1, sticky="nsew")
        right.configure(padding=16)
        ttk.Label(right, text="Bilgi", style="H3.TLabel").pack(anchor="w", pady=(0,8))
        info = ("RAID veri korumasına yardımcı olur ama **yedekleme değildir**. "
                "Denetleyici/işletim/kullanıcı hataları yine veri kaybı doğurabilir. "
                "Her zaman harici ve bağımsız yedekleme yapın.")
        ttk.Label(right, text=info, style="Body.TLabel", wraplength=260, justify="left").pack(anchor="w")

        ttk.Label(right, text="Seçilen RAID açıklaması", style="H3.TLabel")\
            .pack(anchor="w", pady=(14,6))
        self.lbl_brief = ttk.Label(right, text=self.current_brief(), style="Body.TLabel",
                                   wraplength=260, justify="left")
        self.lbl_brief.pack(anchor="w")

    # --- Yardımcı arayüz fonksiyonları ---
    def current_brief(self) -> str:
        label = self.cmb_raid.get() if hasattr(self, "cmb_raid") else RAID_TYPES[0]
        key = label.split(" ")[0] + ("" if key_is_plain(label) else "")  # noop, sadece okunurluk
        base = label.split()[0] + " " + ("")

        # En pratik: baştaki "RAID X" bölümünü çekelim
        head = " ".join(label.split()[:2]) if label.startswith("RAID") else label
        # head -> "RAID 0", "RAID 10", "RAID 50" gibi olur
        return RAID_BRIEFS.get(head, "Bu RAID türü için kısa açıklama bulunamadı.")

    def on_raid_change(self, _event=None):
        self.lbl_brief.configure(text=self.current_brief())

    def on_calc(self):
        self.lbl_warn.configure(text=""); self.lbl_layout.configure(text="")
        try:
            n = int(self.ent_disks.get().strip()); assert n > 0
        except Exception:
            messagebox.showerror("Hata", "Disk sayısı geçerli bir tam sayı olmalı (>=1)."); return
        try:
            size_tb = float(self.ent_size.get().replace(",", ".").strip()); assert size_tb > 0
        except Exception:
            messagebox.showerror("Hata", "Tek disk boyutu geçerli bir sayı olmalı (>0)."); return

        try:
            capacity, speed, fault, warn, layout = calc_raid(n, size_tb, self.cmb_raid.get())
        except ValueError as e:
            messagebox.showerror("Geçersiz yapılandırma", str(e)); return

        self.lbl_capacity.configure(text=f"{human_tb(capacity)} TB")
        self.lbl_speed.configure(text=speed)
        self.lbl_fault.configure(text=fault)
        if layout: self.lbl_layout.configure(text=layout)
        if warn: self.lbl_warn.configure(text=warn)
        # Sağ açıklama, hesap sonrasında da senkron kalsın
        self.on_raid_change()

def key_is_plain(label: str) -> bool:
    return True  # okunurluk için ayraç; ileride varyantlar eklenirse kullanılır

def main():
    app = RaidApp()
    app.mainloop()

if __name__ == "__main__":
    main()