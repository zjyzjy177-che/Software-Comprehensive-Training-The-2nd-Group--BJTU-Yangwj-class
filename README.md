# BJTU Canteen Simulation 🍱

A discrete tick-driven campus dining flow simulation system for Beijing Jiaotong University. Simulates student movement, canteen queuing, and dining behavior based on real campus map and class schedules.

## Features

- **Tick-driven Simulation Engine** — Student FSM (Walking → Queuing → Eating → Leaving) with configurable parameters
- **Multi-Canteen Selection** — Three strategies (distance-first, queue-first, balanced) with dual-factor weighted scoring
- **Real-time Visualization** — Campus map, queue curves, pie charts, BJT clock, notification popups
- **Class Schedule Integration** — Burst student generation based on real BJTU class end times, built-in stagger mode
- **Peak Shift Analysis** — Compare 6 stagger scenarios with metrics on peak queue, wait time, and service volume
- **Report Export** — Excel (.xlsx), Word (.docx), PDF with full statistics and charts
- **Trilingual UI** — Chinese (Simplified/Traditional) + English
- **Cross-platform Packaging** — macOS (.app, .dmg, .pkg) and Windows (.exe)

## Quick Start

```bash
# Dependencies
pip install -r requirements.txt

# Run GUI
python main.py --gui

# Run simulation with visualization
python main.py --tick 500 --vis
```

## Requirements

- Python 3.10+
- Dependencies: `openpyxl`, `python-docx`, `matplotlib`

## Project Structure

```
├── main.py              # Entry point (CLI / GUI)
├── config.py            # Campus coordinates, road network, schedules, parameters
├── models.py            # Student FSM, Window queue, Canteen
├── engine.py            # Core tick-driven simulation loop
├── strategies.py        # Canteen selection algorithm (αβ scoring)
├── road_network.py      # Rectangular road path distance calculation
├── visualizer.py        # Matplotlib real-time rendering
├── gui.py               # Tkinter desktop GUI (~2200 lines)
├── export_report.py     # Excel / Word / PDF report generation
├── peak_shift.py        # Stagger scenario comparison analysis
├── campus_bounds.json   # Building coordinate data
└── assets/              # Icons, maps, resources
```

## How It Works

1. **Simulation Loop** — Each tick (60s real-time) updates all student positions and states
2. **Student Generation** — Burst injection at class end times, controlled by building weights
3. **Canteen Selection** — Score = α × normalized_distance + β × normalized_queue / (windows × service_rate)
4. **Dining Process** — Students walk → queue at window → eat → leave. Non-open hours block new entries
5. **Visualization** — Matplotlib renders map, queue curve, pie chart, and info panel in real-time

## Tech Stack

- Python 3.10+ · Tkinter · Matplotlib · PyInstaller
- openpyxl · python-docx (report export)
- create-dmg · Packages.app (macOS packaging)

## Team

| Member | Role | Contribution |
|--------|------|-------------|
| **Jianyu Zhang** (组长) | Core Engine, Integration, Packaging | 40% |
| **Siming Yue** (组员B) | Configuration, Algorithm, Map Data | 27% |
| **Jiaxin Wei** (组员C) | Visualization, GUI, Windows Build | 33% |

## License

MIT License — see [LICENSE](LICENSE).

---

*Built for the Software Comprehensive Training course at Beijing Jiaotong University, Spring 2026.*
