# ============================================================
#  app.py  -  BusReserve Tkinter Frontend
#  Run: python app.py
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from pyswip import Prolog

# ============================================================
#  PROLOG ENGINE
# ============================================================

prolog = Prolog()
prolog.consult("knowledge_base.pl")

def pl_query(goal):
    try:
        return list(prolog.query(goal))
    except Exception as e:
        print(f"[Prolog error] {goal}\n  {e}")
        return []

def pl_once(goal):
    try:
        return len(list(prolog.query(goal))) > 0
    except Exception as e:
        print(f"[Prolog error] {goal}\n  {e}")
        return False

def decode(val):
    if isinstance(val, bytes):
        return val.decode()
    return str(val)

# ============================================================
#  COLOURS & FONTS
# ============================================================

BG        = "#f0f0f0"
SIDEBAR   = "#e4e4e4"
WHITE     = "#ffffff"
BLUE      = "#2c5f8a"
BLUE_HOV  = "#245079"
TEXT      = "#1a1a1a"
MUTED     = "#555555"
SUCCESS   = "#2e7d32"
ERROR_C   = "#c62828"
WARN_C    = "#e65100"

SEAT_FREE = ("#e8f5e9", "#81c784", "#2e7d32")
SEAT_BOOK = ("#ffebee", "#e57373", "#c62828")
SEAT_BLOK = ("#f5f5f5", "#bbbbbb", "#888888")

FONT      = ("Segoe UI", 10)
FONT_SM   = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_MONO = ("Consolas", 9)

# ============================================================
#  WINDOW
# ============================================================

root = tk.Tk()
root.title("BusReserve - Seat Reservation System")
root.geometry("900x580")
root.resizable(False, False)
root.configure(bg=BG)

titlebar = tk.Frame(root, bg=BLUE, height=36)
titlebar.pack(fill="x")
titlebar.pack_propagate(False)
tk.Label(titlebar, text="  BusReserve  -  Seat Reservation System",
         bg=BLUE, fg="white", font=FONT_BOLD).pack(side="left", pady=8)

body = tk.Frame(root, bg=BG)
body.pack(fill="both", expand=True)

sidebar = tk.Frame(body, bg=SIDEBAR, width=195)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

right = tk.Frame(body, bg=WHITE)
right.pack(side="left", fill="both", expand=True)

topbar = tk.Frame(right, bg=BLUE, height=32)
topbar.pack(fill="x")
topbar.pack_propagate(False)
panel_title = tk.Label(topbar, text="", bg=BLUE, fg="white", font=FONT_BOLD)
panel_title.pack(side="left", padx=12, pady=6)

content = tk.Frame(right, bg=WHITE)
content.pack(fill="both", expand=True)

statusbar = tk.Frame(right, bg="#e4e4e4", height=24)
statusbar.pack(fill="x", side="bottom")
statusbar.pack_propagate(False)
status_left  = tk.Label(statusbar, text="Prolog: connected", bg="#e4e4e4", fg=MUTED, font=FONT_SM)
status_left.pack(side="left", padx=10, pady=3)
status_right = tk.Label(statusbar, text="", bg="#e4e4e4", fg=MUTED, font=FONT_SM)
status_right.pack(side="right", padx=10, pady=3)

# ============================================================
#  OUTPUT LOG
# ============================================================

log_frame = tk.Frame(right, bg=WHITE)
log_frame.pack(side="bottom", fill="x", padx=12, pady=(0, 6))
tk.Label(log_frame, text="Output", bg=WHITE, fg=MUTED, font=FONT_SM).pack(anchor="w")
log_box = tk.Text(log_frame, height=5, font=FONT_MONO, bg="#1e1e1e", fg="#d4d4d4",
                  relief="flat", bd=0, state="disabled", wrap="word")
log_box.pack(fill="x")
log_box.tag_config("ok",   foreground="#4ec9b0")
log_box.tag_config("err",  foreground="#f48771")
log_box.tag_config("info", foreground="#9cdcfe")
log_box.tag_config("warn", foreground="#dcdcaa")

def log(msg, tag="info"):
    log_box.config(state="normal")
    log_box.insert("end", msg + "\n", tag)
    log_box.see("end")
    log_box.config(state="disabled")

def log_clear():
    log_box.config(state="normal")
    log_box.delete("1.0", "end")
    log_box.config(state="disabled")

# ============================================================
#  HELPERS
# ============================================================

def get_buses():
    return [decode(r["Bus"]) for r in pl_query("bus(Bus,_,_,_)")]

def get_bus_label(bus_id):
    r = pl_query(f"bus({bus_id}, From, To, _)")
    if r:
        return f"{bus_id}  ({decode(r[0]['From'])} -> {decode(r[0]['To'])})"
    return bus_id

def get_bus_labels():
    return [get_bus_label(b) for b in get_buses()]

def bus_id_from_label(label):
    return label.split()[0]

def get_passengers():
    """Return list of (id, display_label) for all registered passengers."""
    rows = pl_query("passenger_name(ID, Name)")
    result = []
    for r in rows:
        pid  = decode(r["ID"])
        name = decode(r["Name"])
        # get type and preference for display
        t_r = pl_query(f"passenger_type({pid}, Type)")
        p_r = pl_query(f"preference({pid}, Pref)")
        ptype = decode(t_r[0]["Type"]) if t_r else "?"
        pref  = decode(p_r[0]["Pref"]) if p_r else "?"
        label = f"{pid}  {name}  [{ptype}, {pref}]"
        result.append((pid, label))
    return result

def passenger_id_from_label(label):
    return label.split()[0]

def update_status(bus_id):
    r = pl_query(f"booked_count({bus_id}, Count)")
    count = r[0]["Count"] if r else 0
    total_r = pl_query(f"findall(S, seat({bus_id},S,_,_), Ss), length(Ss, N)")
    total = total_r[0]["N"] if total_r else 5
    status_right.config(text=f"{bus_id}: {count}/{total} booked")

buses      = get_buses()
bus_labels = get_bus_labels()

# ============================================================
#  SEAT MAP
# ============================================================

seatmap_outer = tk.Frame(content, bg=WHITE)
seatmap_outer.pack(fill="x", padx=12, pady=(8, 0))

def refresh_seat_map(bus_id):
    for w in seatmap_outer.winfo_children():
        w.destroy()

    tk.Label(seatmap_outer, text=f"Seat map  -  {bus_id}",
             bg=WHITE, fg=MUTED, font=FONT_SM).pack(anchor="w")

    leg = tk.Frame(seatmap_outer, bg=WHITE)
    leg.pack(anchor="w", pady=(2, 6))
    for lbl, col in [("Free", SUCCESS), ("Booked", ERROR_C), ("Blocked", "#888")]:
        tk.Label(leg, text=f"  {lbl}", bg=WHITE, fg=col, font=FONT_SM).pack(side="left")

    grid_f = tk.Frame(seatmap_outer, bg=WHITE)
    grid_f.pack(anchor="w")

    seats   = pl_query(f"seat({bus_id}, Seat, Row, Type)")
    booked  = [decode(r["Seat"]) for r in pl_query(f"reserved(_, {bus_id}, Seat, _)")]
    blocked = [decode(r["Seat"]) for r in pl_query(f"blocked_seat({bus_id}, Seat, _)")]

    for i, row in enumerate(seats):
        sid   = decode(row["Seat"])
        stype = decode(row["Type"])
        srow  = decode(row["Row"])

        if sid in blocked:
            bg, bd, fg = SEAT_BLOK
        elif sid in booked:
            bg, bd, fg = SEAT_BOOK
        else:
            bg, bd, fg = SEAT_FREE

        outer = tk.Frame(grid_f, bg=bd, padx=1, pady=1)
        outer.grid(row=0, column=i, padx=3)
        tk.Label(outer, text=f"{sid}\n{stype[:3]}\n{srow[:3]}",
                 bg=bg, fg=fg, font=("Segoe UI", 8, "bold"),
                 width=6, pady=4).pack()

    ttk.Separator(seatmap_outer, orient="horizontal").pack(fill="x", pady=6)
    update_status(bus_id)

# ============================================================
#  PANEL SYSTEM
# ============================================================

panels = {}
current_panel = [None]

def show_panel(name, title=None):
    if current_panel[0]:
        current_panel[0].pack_forget()
    panels[name].pack(fill="both", expand=True)
    current_panel[0] = panels[name]
    panel_title.config(text=title or name)
    log_clear()

def make_panel(name):
    f = tk.Frame(content, bg=WHITE)
    panels[name] = f
    return f

# ============================================================
#  SIDEBAR
# ============================================================

active_btn = [None]

def sidebar_btn(text, cmd, section=False):
    if section:
        tk.Label(sidebar, text=text.upper(), bg=SIDEBAR, fg="#999999",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        return None

    def on_click():
        if active_btn[0]:
            active_btn[0].config(bg=SIDEBAR, fg=TEXT)
        btn.config(bg="#d0d8e4", fg=BLUE)
        active_btn[0] = btn
        cmd()

    btn = tk.Label(sidebar, text=f"  {text}", bg=SIDEBAR, fg=TEXT,
                   font=FONT, anchor="w", cursor="hand2", pady=6)
    btn.pack(fill="x")
    btn.bind("<Button-1>", lambda e: on_click())
    btn.bind("<Enter>",    lambda e: btn.config(bg="#dde3ea") if btn is not active_btn[0] else None)
    btn.bind("<Leave>",    lambda e: btn.config(bg=SIDEBAR)   if btn is not active_btn[0] else None)
    return btn

# ============================================================
#  FORM HELPERS
# ============================================================

def form_row(parent, label_text, widget_fn, **kw):
    row = tk.Frame(parent, bg=WHITE)
    row.pack(fill="x", pady=3)
    tk.Label(row, text=label_text, bg=WHITE, fg=MUTED,
             font=FONT_SM, width=16, anchor="w").pack(side="left")
    w = widget_fn(row, **kw)
    w.pack(side="left", fill="x", expand=True)
    return w

def mk_entry(parent, textvariable=None):
    return tk.Entry(parent, font=FONT, relief="solid", bd=1,
                    bg=WHITE, textvariable=textvariable)

def mk_dropdown(parent, values, textvariable=None):
    cb = ttk.Combobox(parent, values=values, state="readonly",
                      font=FONT, textvariable=textvariable)
    if values:
        cb.current(0)
    return cb

def action_btn(parent, text, cmd, color=BLUE):
    def hi(e): btn.config(bg=BLUE_HOV)
    def lo(e): btn.config(bg=color)
    btn = tk.Button(parent, text=text, command=cmd, bg=color, fg="white",
                    font=FONT_BOLD, relief="flat", padx=14, pady=5,
                    cursor="hand2", activebackground=BLUE_HOV, activeforeground="white")
    btn.bind("<Enter>", hi)
    btn.bind("<Leave>", lo)
    return btn

# ============================================================
#  PASSENGER DROPDOWN REFRESH  (called after registration)
# ============================================================

passenger_dropdowns = []   # list of Combobox widgets to keep in sync

def refresh_passenger_dropdowns():
    labels = [lbl for _, lbl in get_passengers()]
    for cb in passenger_dropdowns:
        cb["values"] = labels
        if labels and not cb.get():
            cb.current(0)

# ============================================================
#  PANEL: REGISTER PASSENGER
# ============================================================

p_register = make_panel("register")

reg_name_var = tk.StringVar()
reg_age_var  = tk.StringVar()
reg_pref_var = tk.StringVar()

def do_register():
    name = reg_name_var.get().strip()
    age_s = reg_age_var.get().strip()
    pref  = reg_pref_var.get().strip()

    if not name or not age_s:
        log("Name and age are required.", "warn")
        return
    try:
        age = int(age_s)
    except ValueError:
        log("Age must be a number.", "warn")
        return
    if pref not in ("window", "aisle", "none"):
        log("Select a valid preference.", "warn")
        return

    # derive type for display
    if age >= 60:
        ptype = "elderly"
    elif age <= 12:
        ptype = "child"
    elif age < 26:
        ptype = "student"
    else:
        ptype = "normal"

    pref_atom = "no_preference" if pref == "none" else pref

    # escape name for Prolog atom using single quotes
    safe_name = name.replace("'", "\\'")
    goal = f"register_passenger('{safe_name}', {age}, {pref_atom}, ID)"
    r = pl_query(goal)

    if r:
        new_id = decode(r[0]["ID"])
        log(f"Registered: {new_id}  {name}  [type: {ptype}, pref: {pref}]", "ok")
        refresh_passenger_dropdowns()
        reg_name_var.set("")
        reg_age_var.set("")
    else:
        log("Registration failed.", "err")

tk.Label(p_register, text="Fill in passenger details below.",
         bg=WHITE, fg=MUTED, font=FONT_SM).pack(anchor="w", padx=12, pady=(10,4))

reg_f = tk.Frame(p_register, bg=WHITE, padx=12)
reg_f.pack(fill="x")

form_row(reg_f, "Full name",       mk_entry,   textvariable=reg_name_var)
form_row(reg_f, "Age",             mk_entry,   textvariable=reg_age_var)

# preference dropdown
pref_row = tk.Frame(reg_f, bg=WHITE)
pref_row.pack(fill="x", pady=3)
tk.Label(pref_row, text="Seat preference", bg=WHITE, fg=MUTED,
         font=FONT_SM, width=16, anchor="w").pack(side="left")
pref_cb = ttk.Combobox(pref_row, values=["window", "aisle", "none"],
                        textvariable=reg_pref_var, state="readonly", font=FONT)
pref_cb.current(0)
pref_cb.pack(side="left", fill="x", expand=True)

# info label showing derived type
info_lbl = tk.Label(reg_f, text="", bg=WHITE, fg="#888", font=FONT_SM)
info_lbl.pack(anchor="w", pady=(4,0))

def on_age_change(*_):
    try:
        age = int(reg_age_var.get())
        if age >= 60:   t = "elderly  (front seat priority)"
        elif age <= 12: t = "child  (front seat priority)"
        elif age < 26:  t = "student"
        else:           t = "normal"
        info_lbl.config(text=f"  Passenger type: {t}")
    except ValueError:
        info_lbl.config(text="")

reg_age_var.trace_add("write", on_age_change)

reg_btn_row = tk.Frame(p_register, bg=WHITE, padx=12)
reg_btn_row.pack(fill="x", pady=8)
action_btn(reg_btn_row, "Register Passenger", do_register).pack(side="left")

# ============================================================
#  PANEL: BOOK A SEAT
# ============================================================

p_book = make_panel("book")

bus_var_book  = tk.StringVar()
pass_var_book = tk.StringVar()
seat_var_book = tk.StringVar()

def on_bus_change_book(*_):
    bid = bus_id_from_label(bus_var_book.get())
    refresh_seat_map(bid)

def do_book():
    bus_label  = bus_var_book.get()
    pass_label = pass_var_book.get()
    seat       = seat_var_book.get().strip()

    if not bus_label or not pass_label or not seat:
        log("Select a bus, passenger and enter a seat ID.", "warn")
        return

    bus = bus_id_from_label(bus_label)
    pid = passenger_id_from_label(pass_label)

    # check blacklist first
    if pl_query(f"blacklisted({pid})"):
        log(f"[DENIED] {pid} is blacklisted.", "err")
        return

    # check availability
    if not pl_query(f"available_seat({bus}, {seat})"):
        log(f"[DENIED] Seat {seat} on {bus} is not available.", "err")
        return

    pl_once(f"book_seat({bus}, {seat}, {pid})")
    r = pl_query(f"reserved(ID, {bus}, {seat}, {pid})")
    if r:
        bid = decode(r[0]["ID"])
        log(f"Booked!  {bid}  |  {bus}  seat {seat}  |  {pid}", "ok")
        refresh_seat_map(bus)
    else:
        log("Booking failed unexpectedly.", "err")

# Bus row
bus_row_b = tk.Frame(p_book, bg=WHITE)
bus_row_b.pack(fill="x", padx=12, pady=(8, 0))
tk.Label(bus_row_b, text="Bus", bg=WHITE, fg=MUTED, font=FONT_SM,
         width=16, anchor="w").pack(side="left")
bus_cb_book = ttk.Combobox(bus_row_b, values=bus_labels,
                            textvariable=bus_var_book, state="readonly", font=FONT)
if bus_labels:
    bus_cb_book.current(0)
bus_cb_book.pack(side="left", fill="x", expand=True)
bus_cb_book.bind("<<ComboboxSelected>>", on_bus_change_book)

# Passenger dropdown
pass_row_b = tk.Frame(p_book, bg=WHITE)
pass_row_b.pack(fill="x", padx=12, pady=3)
tk.Label(pass_row_b, text="Passenger", bg=WHITE, fg=MUTED, font=FONT_SM,
         width=16, anchor="w").pack(side="left")
pass_cb_book = ttk.Combobox(pass_row_b, textvariable=pass_var_book,
                             state="readonly", font=FONT)
pass_cb_book.pack(side="left", fill="x", expand=True)
passenger_dropdowns.append(pass_cb_book)

# Seat entry
seat_row_b = tk.Frame(p_book, bg=WHITE)
seat_row_b.pack(fill="x", padx=12, pady=3)
tk.Label(seat_row_b, text="Seat ID", bg=WHITE, fg=MUTED, font=FONT_SM,
         width=16, anchor="w").pack(side="left")
tk.Entry(seat_row_b, font=FONT, relief="solid", bd=1, bg=WHITE,
         textvariable=seat_var_book).pack(side="left", fill="x", expand=True)

book_btn_row = tk.Frame(p_book, bg=WHITE, padx=12)
book_btn_row.pack(fill="x", pady=6)
action_btn(book_btn_row, "Book Seat", do_book).pack(side="left", padx=(0,8))
tk.Button(book_btn_row, text="Clear", command=lambda: (seat_var_book.set(""), log_clear()),
          bg="#e0e0e0", fg=TEXT, font=FONT, relief="flat",
          padx=10, pady=5, cursor="hand2").pack(side="left")

# ============================================================
#  PANEL: CANCEL BOOKING
# ============================================================

p_cancel = make_panel("cancel")

cancel_id_var = tk.StringVar()

def do_cancel():
    bid = cancel_id_var.get().strip()
    if not bid:
        log("Enter a Booking ID.", "warn")
        return
    r = pl_query(f"reserved({bid}, Bus, Seat, P)")
    if not r:
        log(f"No booking found: {bid}", "err")
        return
    bus  = decode(r[0]["Bus"])
    seat = decode(r[0]["Seat"])
    pax  = decode(r[0]["P"])
    pl_once(f"cancel_booking({bid})")
    log(f"Cancelled  {bid}  |  {bus}  seat {seat}  |  {pax}", "ok")
    cancel_id_var.set("")
    refresh_seat_map(bus)

tk.Label(p_cancel, text="Enter the Booking ID to cancel (e.g. B101).",
         bg=WHITE, fg=MUTED, font=FONT_SM).pack(anchor="w", padx=12, pady=(10,4))

can_f = tk.Frame(p_cancel, bg=WHITE, padx=12)
can_f.pack(fill="x")
form_row(can_f, "Booking ID", mk_entry, textvariable=cancel_id_var)

can_btn_row = tk.Frame(p_cancel, bg=WHITE, padx=12)
can_btn_row.pack(fill="x", pady=6)
action_btn(can_btn_row, "Cancel Booking", do_cancel, color="#b71c1c").pack(side="left")

# ============================================================
#  PANEL: CHANGE SEAT
# ============================================================

p_change = make_panel("change")

bus_var_chg  = tk.StringVar()
pass_var_chg = tk.StringVar()
old_var_chg  = tk.StringVar()
new_var_chg  = tk.StringVar()

def on_bus_change_chg(*_):
    refresh_seat_map(bus_id_from_label(bus_var_chg.get()))

def do_change():
    bus  = bus_id_from_label(bus_var_chg.get())
    pid  = passenger_id_from_label(pass_var_chg.get())
    old_s = old_var_chg.get().strip()
    new_s = new_var_chg.get().strip()
    if not old_s or not new_s:
        log("Enter both current and new seat IDs.", "warn")
        return
    if not pl_query(f"reserved(_, {bus}, {old_s}, {pid})"):
        log(f"No booking found for {pid} on seat {old_s} ({bus}).", "err")
        return
    if not pl_query(f"available_seat({bus}, {new_s})"):
        log(f"Seat {new_s} is not available on {bus}.", "err")
        return
    pl_once(f"change_seat({bus}, {old_s}, {new_s}, {pid})")
    log(f"Changed: {pid}  {old_s} -> {new_s}  on {bus}", "ok")
    refresh_seat_map(bus)

chg_bus_row = tk.Frame(p_change, bg=WHITE)
chg_bus_row.pack(fill="x", padx=12, pady=(8,0))
tk.Label(chg_bus_row, text="Bus", bg=WHITE, fg=MUTED, font=FONT_SM,
         width=16, anchor="w").pack(side="left")
chg_cb = ttk.Combobox(chg_bus_row, values=bus_labels, textvariable=bus_var_chg,
                       state="readonly", font=FONT)
if bus_labels: chg_cb.current(0)
chg_cb.pack(side="left", fill="x", expand=True)
chg_cb.bind("<<ComboboxSelected>>", on_bus_change_chg)

chg_pass_row = tk.Frame(p_change, bg=WHITE)
chg_pass_row.pack(fill="x", padx=12, pady=3)
tk.Label(chg_pass_row, text="Passenger", bg=WHITE, fg=MUTED, font=FONT_SM,
         width=16, anchor="w").pack(side="left")
chg_pass_cb = ttk.Combobox(chg_pass_row, textvariable=pass_var_chg,
                             state="readonly", font=FONT)
chg_pass_cb.pack(side="left", fill="x", expand=True)
passenger_dropdowns.append(chg_pass_cb)

chg_f = tk.Frame(p_change, bg=WHITE, padx=12)
chg_f.pack(fill="x", pady=4)
form_row(chg_f, "Current seat", mk_entry, textvariable=old_var_chg)
form_row(chg_f, "New seat",     mk_entry, textvariable=new_var_chg)

chg_btn_row = tk.Frame(p_change, bg=WHITE, padx=12)
chg_btn_row.pack(fill="x", pady=6)
action_btn(chg_btn_row, "Change Seat", do_change).pack(side="left")

# ============================================================
#  PANEL: RECOMMEND SEAT
# ============================================================

p_rec = make_panel("recommend")

bus_var_rec  = tk.StringVar()
pass_var_rec = tk.StringVar()

def on_bus_change_rec(*_):
    refresh_seat_map(bus_id_from_label(bus_var_rec.get()))

def do_recommend():
    bus        = bus_id_from_label(bus_var_rec.get())
    pass_label = pass_var_rec.get()
    if not pass_label:
        log("Select a passenger.", "warn")
        return
    pid = passenger_id_from_label(pass_label)

    # show why — pull type and preference
    t_r = pl_query(f"passenger_type({pid}, Type)")
    p_r = pl_query(f"preference({pid}, Pref)")
    n_r = pl_query(f"passenger_name({pid}, Name)")
    ptype = decode(t_r[0]["Type"]) if t_r else "unknown"
    ppref = decode(p_r[0]["Pref"]) if p_r else "none"
    pname = decode(n_r[0]["Name"]) if n_r else pid

    log(f"Passenger: {pname}  |  type: {ptype}  |  preference: {ppref}", "info")

    r = pl_query(f"recommend_seat({pid}, {bus}, Seat)")
    if r:
        seat = decode(r[0]["Seat"])
        # explain the match
        if ptype in ("elderly", "child"):
            reason = "front seat (priority for elderly/child)"
        elif ppref in ("window", "aisle"):
            reason = f"{ppref} seat (matches preference)"
        else:
            reason = "first available seat"
        log(f"Recommended: {seat}  on {bus}  ({reason})", "ok")
        refresh_seat_map(bus)
    else:
        log(f"No seats available on {bus}.", "err")

rec_bus_row = tk.Frame(p_rec, bg=WHITE)
rec_bus_row.pack(fill="x", padx=12, pady=(8,0))
tk.Label(rec_bus_row, text="Bus", bg=WHITE, fg=MUTED, font=FONT_SM,
         width=16, anchor="w").pack(side="left")
rec_cb = ttk.Combobox(rec_bus_row, values=bus_labels, textvariable=bus_var_rec,
                       state="readonly", font=FONT)
if bus_labels: rec_cb.current(0)
rec_cb.pack(side="left", fill="x", expand=True)
rec_cb.bind("<<ComboboxSelected>>", on_bus_change_rec)

rec_pass_row = tk.Frame(p_rec, bg=WHITE)
rec_pass_row.pack(fill="x", padx=12, pady=3)
tk.Label(rec_pass_row, text="Passenger", bg=WHITE, fg=MUTED, font=FONT_SM,
         width=16, anchor="w").pack(side="left")
rec_pass_cb = ttk.Combobox(rec_pass_row, textvariable=pass_var_rec,
                             state="readonly", font=FONT)
rec_pass_cb.pack(side="left", fill="x", expand=True)
passenger_dropdowns.append(rec_pass_cb)

rec_btn_row = tk.Frame(p_rec, bg=WHITE, padx=12)
rec_btn_row.pack(fill="x", pady=6)
action_btn(rec_btn_row, "Recommend", do_recommend).pack(side="left")

# ============================================================
#  PANEL: ALL BOOKINGS
# ============================================================

p_all = make_panel("all_bookings")

def refresh_all_bookings():
    for w in p_all.winfo_children():
        w.destroy()

    tk.Label(p_all, text="All current bookings",
             bg=WHITE, fg=MUTED, font=FONT_SM).pack(anchor="w", padx=12, pady=(10,4))

    cols = ("Booking ID", "Bus", "Seat", "Passenger ID", "Passenger Name")
    tree = ttk.Treeview(p_all, columns=cols, show="headings", height=10)
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=130, anchor="center")
    tree.pack(fill="both", expand=True, padx=12, pady=(0,8))

    results = pl_query("reserved(ID, Bus, Seat, P)")
    if not results:
        log("No bookings in the system yet.", "info")
    for r in results:
        pid   = decode(r["P"])
        n_r   = pl_query(f"passenger_name({pid}, Name)")
        pname = decode(n_r[0]["Name"]) if n_r else "Unknown"
        tree.insert("", "end", values=(
            decode(r["ID"]), decode(r["Bus"]),
            decode(r["Seat"]), pid, pname
        ))

# ============================================================
#  PANEL: AVAILABLE SEATS
# ============================================================

p_avail = make_panel("available")

bus_var_avail = tk.StringVar()

def do_avail():
    bus = bus_id_from_label(bus_var_avail.get())
    r = pl_query(f"findall(S, available_seat({bus}, S), List)")
    seats = [decode(s) for s in r[0]["List"]] if r and r[0]["List"] else []
    refresh_seat_map(bus)
    if seats:
        log(f"Available on {bus}: {', '.join(seats)}", "ok")
    else:
        log(f"No seats available on {bus}.", "err")

av_bus_row = tk.Frame(p_avail, bg=WHITE)
av_bus_row.pack(fill="x", padx=12, pady=(8,0))
tk.Label(av_bus_row, text="Bus", bg=WHITE, fg=MUTED, font=FONT_SM,
         width=16, anchor="w").pack(side="left")
av_cb = ttk.Combobox(av_bus_row, values=bus_labels, textvariable=bus_var_avail,
                      state="readonly", font=FONT)
if bus_labels: av_cb.current(0)
av_cb.pack(side="left", fill="x", expand=True)

av_btn_row = tk.Frame(p_avail, bg=WHITE, padx=12)
av_btn_row.pack(fill="x", pady=8)
action_btn(av_btn_row, "Check", do_avail).pack(side="left")

# ============================================================
#  PANEL: BLOCK / UNBLOCK
# ============================================================

p_block = make_panel("block")

bus_var_blk    = tk.StringVar()
seat_var_blk   = tk.StringVar()
reason_var_blk = tk.StringVar()

def on_bus_change_blk(*_):
    refresh_seat_map(bus_id_from_label(bus_var_blk.get()))

def do_block():
    bus    = bus_id_from_label(bus_var_blk.get())
    seat   = seat_var_blk.get().strip()
    reason = reason_var_blk.get().strip() or "maintenance"
    if not seat:
        log("Enter a Seat ID.", "warn")
        return
    pl_once(f"block_seat({bus}, {seat}, {reason})")
    log(f"Blocked  {seat}  on {bus}  ({reason})", "warn")
    refresh_seat_map(bus)

def do_unblock():
    bus  = bus_id_from_label(bus_var_blk.get())
    seat = seat_var_blk.get().strip()
    if not seat:
        log("Enter a Seat ID.", "warn")
        return
    pl_once(f"unblock_seat({bus}, {seat})")
    log(f"Unblocked  {seat}  on {bus}", "ok")
    refresh_seat_map(bus)

blk_bus_row = tk.Frame(p_block, bg=WHITE)
blk_bus_row.pack(fill="x", padx=12, pady=(8,0))
tk.Label(blk_bus_row, text="Bus", bg=WHITE, fg=MUTED, font=FONT_SM,
         width=16, anchor="w").pack(side="left")
blk_cb = ttk.Combobox(blk_bus_row, values=bus_labels, textvariable=bus_var_blk,
                       state="readonly", font=FONT)
if bus_labels: blk_cb.current(0)
blk_cb.pack(side="left", fill="x", expand=True)
blk_cb.bind("<<ComboboxSelected>>", on_bus_change_blk)

blk_f = tk.Frame(p_block, bg=WHITE, padx=12)
blk_f.pack(fill="x", pady=4)
form_row(blk_f, "Seat ID",         mk_entry, textvariable=seat_var_blk)
form_row(blk_f, "Reason (block)",  mk_entry, textvariable=reason_var_blk)

blk_btn_row = tk.Frame(p_block, bg=WHITE, padx=12)
blk_btn_row.pack(fill="x", pady=6)
action_btn(blk_btn_row, "Block Seat",   do_block,   color=WARN_C).pack(side="left", padx=(0,8))
action_btn(blk_btn_row, "Unblock Seat", do_unblock, color=SUCCESS).pack(side="left")

# ============================================================
#  PANEL: BLACKLIST
# ============================================================

p_black = make_panel("blacklist")

pass_var_black = tk.StringVar()

def do_blacklist():
    pass_label = pass_var_black.get()
    if not pass_label:
        log("Select a passenger.", "warn")
        return
    pid = passenger_id_from_label(pass_label)
    already = pl_query(f"blacklisted({pid})")
    pl_once(f"add_to_blacklist({pid})")
    if already:
        log(f"{pid} is already blacklisted.", "warn")
    else:
        log(f"{pid} has been blacklisted.", "err")

tk.Label(p_black, text="Select a passenger to blacklist.",
         bg=WHITE, fg=MUTED, font=FONT_SM).pack(anchor="w", padx=12, pady=(10,4))

blk2_pass_row = tk.Frame(p_black, bg=WHITE)
blk2_pass_row.pack(fill="x", padx=12, pady=3)
tk.Label(blk2_pass_row, text="Passenger", bg=WHITE, fg=MUTED, font=FONT_SM,
         width=16, anchor="w").pack(side="left")
blk2_pass_cb = ttk.Combobox(blk2_pass_row, textvariable=pass_var_black,
                              state="readonly", font=FONT)
blk2_pass_cb.pack(side="left", fill="x", expand=True)
passenger_dropdowns.append(blk2_pass_cb)

blk2_btn_row = tk.Frame(p_black, bg=WHITE, padx=12)
blk2_btn_row.pack(fill="x", pady=8)
action_btn(blk2_btn_row, "Blacklist", do_blacklist, color="#b71c1c").pack(side="left")

# ============================================================
#  PANEL: WAITING LIST
# ============================================================

p_wait = make_panel("waiting")

bus_var_wait  = tk.StringVar()
pass_var_wait = tk.StringVar()

def do_add_wait():
    bus        = bus_id_from_label(bus_var_wait.get())
    pass_label = pass_var_wait.get()
    if not pass_label:
        log("Select a passenger.", "warn")
        return
    pid = passenger_id_from_label(pass_label)
    pl_once(f"handle_full_bus({bus}, {pid})")
    r = pl_query(f"findall(P, waiting_list({bus}, P), List)")
    waiting = [decode(s) for s in r[0]["List"]] if r and r[0]["List"] else []
    if waiting:
        log(f"Waiting list for {bus}: {', '.join(waiting)}", "info")
    else:
        log(f"{bus} still has available seats.", "ok")

wait_bus_row = tk.Frame(p_wait, bg=WHITE)
wait_bus_row.pack(fill="x", padx=12, pady=(8,0))
tk.Label(wait_bus_row, text="Bus", bg=WHITE, fg=MUTED, font=FONT_SM,
         width=16, anchor="w").pack(side="left")
wait_cb = ttk.Combobox(wait_bus_row, values=bus_labels, textvariable=bus_var_wait,
                        state="readonly", font=FONT)
if bus_labels: wait_cb.current(0)
wait_cb.pack(side="left", fill="x", expand=True)

wait_pass_row = tk.Frame(p_wait, bg=WHITE)
wait_pass_row.pack(fill="x", padx=12, pady=3)
tk.Label(wait_pass_row, text="Passenger", bg=WHITE, fg=MUTED, font=FONT_SM,
         width=16, anchor="w").pack(side="left")
wait_pass_cb = ttk.Combobox(wait_pass_row, textvariable=pass_var_wait,
                              state="readonly", font=FONT)
wait_pass_cb.pack(side="left", fill="x", expand=True)
passenger_dropdowns.append(wait_pass_cb)

wait_btn_row = tk.Frame(p_wait, bg=WHITE, padx=12)
wait_btn_row.pack(fill="x", pady=6)
action_btn(wait_btn_row, "Add to Waiting List", do_add_wait).pack(side="left")

# ============================================================
#  WIRE UP SIDEBAR
# ============================================================

sidebar_btn("Passengers", None, section=True)
sidebar_btn("Register passenger", lambda: show_panel("register", "Register passenger"))

sidebar_btn("Bookings", None, section=True)
sidebar_btn("Book seat",      lambda: (show_panel("book",     "Book a seat"),
                                       refresh_seat_map(bus_id_from_label(bus_var_book.get()))))
sidebar_btn("Cancel booking", lambda: show_panel("cancel",   "Cancel booking"))
sidebar_btn("Change seat",    lambda: (show_panel("change",   "Change seat"),
                                       refresh_seat_map(bus_id_from_label(bus_var_chg.get()))))
sidebar_btn("Recommend seat", lambda: (show_panel("recommend","Recommend a seat"),
                                       refresh_seat_map(bus_id_from_label(bus_var_rec.get()))))

sidebar_btn("Reports", None, section=True)
sidebar_btn("All bookings",    lambda: (show_panel("all_bookings", "All bookings"),
                                        refresh_all_bookings()))
sidebar_btn("Available seats", lambda: (show_panel("available",   "Available seats"),
                                        refresh_seat_map(bus_id_from_label(bus_var_avail.get()))))

sidebar_btn("Admin", None, section=True)
sidebar_btn("Block / unblock", lambda: (show_panel("block",     "Block / unblock seat"),
                                        refresh_seat_map(bus_id_from_label(bus_var_blk.get()))))
sidebar_btn("Blacklist",       lambda: show_panel("blacklist",  "Blacklist passenger"))
sidebar_btn("Waiting list",    lambda: show_panel("waiting",    "Waiting list"))

# ============================================================
#  LAUNCH
# ============================================================

# populate all passenger dropdowns with seed passengers
refresh_passenger_dropdowns()

# start on register panel so first thing user does is add a passenger
show_panel("register", "Register passenger")
if buses:
    refresh_seat_map(buses[0])

root.mainloop()