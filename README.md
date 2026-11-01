# ♟️ Chess Advisor

### - Choose White or Black
### - Replicate your opponent's moves on the board, and see your responses.

## Requirements

- Python 3.9+
- [Stockfish](https://stockfishchess.org/download/)
- `python-chess`

## Installation

### Windows

Install Python and download the Stockfish executable. Then run:

```powershell
py -m pip install python-chess
```

Set `ENGINE_PATH` in `chess_advisor.py` to the downloaded Stockfish executable's full path.

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install stockfish python3-venv -y
python3 -m venv .venv
source .venv/bin/activate
pip install python-chess
```

### macOS

```bash
brew install stockfish
python3 -m venv .venv
source .venv/bin/activate
pip install python-chess
```

If Stockfish is not automatically detected, set `ENGINE_PATH` in `chess_advisor.py` to its executable path (find it with `which stockfish` on Linux/macOS).

## Run

```bash
python chess_advisor.py
```

Use `python3 chess_advisor.py` on systems where `python` is unavailable.

Open **http://127.0.0.1:8765** in your browser.



Intended for practice, analysis, and games where engine assistance is permitted.
