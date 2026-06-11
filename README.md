# BusReserve — Prolog Bus Seat Reservation System

A rule-based expert system for bus seat reservations built with SWI-Prolog and Python Tkinter.
The Prolog knowledge base handles all logic (booking rules, seat recommendations, blacklisting)
while the Tkinter frontend provides a clean desktop GUI.

---

## Project Structure

```
bus-reservation-prolog/
├── knowledge.pl      # Prolog knowledge base — all facts, rules, and logic
├── app.py            # Python Tkinter frontend — connects to Prolog via PySwip
└── README.md
```

---

## Prerequisites

Make sure you have all three installed before running:

| Tool | Version | Download |
|---|---|---|
| SWI-Prolog | 10.x | https://www.swi-prolog.org/download/stable |
| Python | 3.8+ | https://www.python.org/downloads |
| PySwip | latest | `pip install pyswip` |

---

## Installation

### 1. Install SWI-Prolog

Download and install from https://www.swi-prolog.org/download/stable

**Windows:** During installation, tick **"Add SWI-Prolog to PATH"**

Verify the install:
```bash
swipl --version
```

If `swipl` is not recognized after install, add it to PATH manually:
- Search **"Environment Variables"** in the Windows start menu
- Under System Variables, find **Path** and click Edit
- Add: `C:\Program Files\swipl\bin`
- Restart your terminal

---

### 2. Install Python dependencies

```bash
pip install pyswip
```

Verify PySwip works:
```bash
python -c "from pyswip import Prolog; print('PySwip OK')"
```

If you get a `libswipl` error on Windows, run this in PowerShell then restart VS Code:
```powershell
[System.Environment]::SetEnvironmentVariable("SWI_HOME_DIR","C:\Program Files\swipl","User")
```

---

### 3. Clone the repository

```bash
git clone https://github.com/M-Thanu/bus-reservation-prolog.git
cd bus-reservation-prolog
```

---

## Running the Application

Make sure `knowledge.pl` and `app.py` are in the **same folder**, then run:

```bash
python app.py
```

The desktop window will open automatically.

---

## Using the Application

### Step 1 — Register a passenger
The app opens on the **Register Passenger** panel.
Enter the passenger's name, age, and seat preference (window / aisle / none).
The system automatically assigns a passenger ID and determines the passenger type:

| Age | Assigned Type |
|---|---|
| 12 and under | child |
| 13 – 25 | student |
| 26 – 59 | normal |
| 60 and above | elderly |

Elderly and child passengers are automatically prioritised for front seats when using seat recommendation.

---

### Step 2 — Book a seat
Go to **Book Seat** in the sidebar.
- Select a bus from the dropdown
- Select a registered passenger from the dropdown
- Enter a seat ID (e.g. `s1`, `s2`) — refer to the live seat map
- Click **Book Seat**

The seat map updates immediately after every booking.

---

### Step 3 — Other features

| Panel | What it does |
|---|---|
| Recommend seat | Suggests the best seat based on passenger type and preference |
| Cancel booking | Enter a Booking ID (e.g. `B101`) to cancel |
| Change seat | Move a passenger from one seat to another |
| All bookings | Table view of every active booking |
| Available seats | Lists all free seats on a selected bus |
| Block / Unblock | Admin: block a seat with a reason, or unblock it |
| Blacklist | Prevent a passenger from making bookings |
| Waiting list | Add a passenger to the waiting list when a bus is full |

---

## Prolog Concepts Covered

| Concept | Where used |
|---|---|
| Facts | `bus/4`, `seat/4`, `near/2` |
| Rules and Horn clauses | `available_seat/2`, `suitable_seat/3`, `recommend_seat/3` |
| Dynamic knowledge base | `reserved/4`, `passenger_type/2`, `preference/2` |
| `assertz` | `book_seat/3`, `register_passenger/4`, `block_seat/3` |
| `retract` | `cancel_booking/1`, `next_booking_id/1`, `unblock_seat/2` |
| Backtracking and `fail` | `show_all_bookings/0` |
| Negation as failure `\+` | `available_seat/2`, `can_book/3` |
| Cut `!` | `can_book/3`, `recommend_seat/3`, `age_to_type/2` |
| If-then-else `-> ;` | `book_seat/3`, `cancel_booking/1`, `handle_full_bus/2` |
| `findall/3` | `show_available_seats/1`, `booked_count/2` |
| Arithmetic and `is` | `next_booking_id/1`, `next_passenger_id/1` |
| `format/2` | All output predicates |
| `read_line_to_string` | CLI input helpers |
| `atom_concat` | ID generation (`B101`, `p005`) |

---

## Example Workflow

```
1. Register:  Amara Silva, age 65, preference window
   → ID: p005  type: elderly  preference: window

2. Recommend: select p005 on bus101
   → Recommended: s1  (front seat — priority for elderly)

3. Book:      select p005, bus101, seat s1
   → Booked!  B101 | bus101 | seat s1 | p005

4. All bookings:
   → B101 | bus101 | s1 | p005 | Amara Silva
```

---

## CLI Mode (optional)

You can also run the Prolog knowledge base directly in the terminal without the GUI:

```bash
swipl knowledge.pl
```

Then at the Prolog prompt:

```prolog
start.
```

---

## Built With

- [SWI-Prolog](https://www.swi-prolog.org/) — logic engine and knowledge base
- [PySwip](https://github.com/yuce/pyswip) — Python bridge to SWI-Prolog
- [Tkinter](https://docs.python.org/3/library/tkinter.html) — Python standard library GUI
