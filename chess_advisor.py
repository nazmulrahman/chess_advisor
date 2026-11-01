
#!/usr/bin/env python3
import json
import shutil
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import chess
import chess.engine

HOST = "127.0.0.1"
PORT = 8765
ENGINE_PATH = shutil.which("stockfish") or "/usr/games/stockfish"

board = chess.Board()
player = chess.WHITE
lock = threading.RLock()

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chess Advisor</title>
<style>
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 24px;
  background: #10151e;
  color: #edf3fc;
  font-family: system-ui, sans-serif;
}
header {
  max-width: 1100px;
  margin: 0 auto 22px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
h1 { margin: 0; font-size: 26px; }
small, .muted { color: #a7b4c5; }
main {
  max-width: 1100px;
  margin: auto;
  display: grid;
  grid-template-columns: minmax(300px, 590px) 1fr;
  gap: 24px;
}
.panel {
  background: #1c2531;
  border: 1px solid #344052;
  border-radius: 16px;
  padding: 20px;
}
.board {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: 8px;
}
.square {
  position: relative;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  border-radius: 0;
  font: 52px "DejaVu Sans", "Segoe UI Symbol", serif;
  cursor: pointer;
}
.light { background: #eeeed2; }
.dark { background: #769656; }
.selected { background: #f2d15c !important; }
.target::after {
  content: "";
  position: absolute;
  width: 24%;
  height: 24%;
  background: #22502988;
  border-radius: 50%;
}
.from { box-shadow: inset 0 0 0 5px #f8c94d; }
.to { box-shadow: inset 0 0 0 5px #27d6a0; }
.piece { z-index: 1; line-height: 1; }
.whitepiece {
  color: #fffdf5;
  -webkit-text-stroke: 1px #181818;
  text-shadow: 0 2px 2px #0005;
}
.blackpiece {
  color: #161a22;
  -webkit-text-stroke: .6px white;
}
.coord {
  position: absolute;
  bottom: 2px;
  right: 4px;
  font: 10px system-ui;
  color: #222a;
}
button, select {
  background: #303c4e;
  color: white;
  border: 1px solid #4b5b70;
  padding: 11px 13px;
  border-radius: 9px;
  cursor: pointer;
}
button:hover { background: #42536a; }
.controls {
  display: flex;
  gap: 10px;
  margin: 15px 0;
  flex-wrap: wrap;
}
.green { color: #68e8a8; }
.bigmove {
  font-size: 47px;
  font-weight: 800;
  margin: 12px 0;
}
.section {
  border-top: 1px solid #344052;
  padding-top: 18px;
  margin-top: 22px;
}
.status { margin-top: 14px; min-height: 25px; }
.history {
  background: #121a25;
  border-radius: 8px;
  padding: 12px;
  line-height: 2;
  max-height: 180px;
  overflow: auto;
}
.notice {
  background: #273443;
  border-radius: 8px;
  padding: 12px;
  color: #b8c8db;
  font-size: 13px;
}
#error { color: #ff9b9b; }
#promotion { display: none; gap: 7px; }
@media(max-width: 800px) {
  main { grid-template-columns: 1fr; }
  body { padding: 12px; }
  .square { font-size: clamp(26px, 7vw, 52px); }
}
</style>
</head>
<body>

<header>
 <div>
  <h1>♟ Chess Advisor</h1>
  <small>Local Stockfish Analysis</small>
 </div>
 <span class="green">● ENGINE READY</span>
</header>

<main>
<section class="panel">
 <div style="display:flex;justify-content:space-between;
             align-items:center;margin-bottom:16px">
  <label>Your side:
   <select id="color">
    <option value="white">White</option>
    <option value="black">Black</option>
   </select>
  </label>
  <span id="turn" class="muted"></span>
 </div>

 <div id="board" class="board"></div>
 <div class="status" id="status"></div>

 <div id="promotion">
  <button data-promo="q">Queen</button>
  <button data-promo="r">Rook</button>
  <button data-promo="b">Bishop</button>
  <button data-promo="n">Knight</button>
 </div>

 <div class="controls">
  <button id="undo">Undo</button>
  <button id="reset">New Game</button>
 </div>

 <div class="notice">
  Click your opponent's piece and destination square.
  Stockfish automatically plays your side after analysis.
  You only enter your opponent's moves.
 </div>
</section>

<aside class="panel">
 <div class="muted">STOCKFISH RECOMMENDATION</div>
 <div id="suggestion" class="bigmove green">—</div>
 <div id="description" class="muted">
  Waiting for analysis...
 </div>

 <div class="section">
  <label>Engine thinking time</label>
  <select id="think">
   <option value="0.2">Fast — 0.2 sec</option>
   <option value="0.5" selected>Balanced — 0.5 sec</option>
   <option value="1.5">Strong — 1.5 sec</option>
   <option value="3">Deep — 3 sec</option>
  </select>
  <p id="score" class="muted">Evaluation: —</p>
 </div>

 <div class="section">
  <h3>Move History</h3>
  <div id="history" class="history">No moves yet.</div>
 </div>

 <div class="section">
  <h3>FEN</h3>
  <small id="fen" style="overflow-wrap:anywhere"></small>
 </div>

 <p id="error"></p>
</aside>
</main>

<script>
const glyph = {
 K:"♔", Q:"♕", R:"♖", B:"♗", N:"♘", P:"♙",
 k:"♚", q:"♛", r:"♜", b:"♝", n:"♞", p:"♟"
};

let state = null;
let selected = null;
let pending = null;
let lastMove = null;
let requestId = 0;

const $ = id => document.getElementById(id);

async function api(path, data) {
 const opts = data === undefined ? {} : {
  method:"POST",
  headers:{"Content-Type":"application/json"},
  body:JSON.stringify(data)
 };
 const res = await fetch(path, opts);
 const value = await res.json();
 if(!res.ok) throw Error(value.error || "Request failed");
 return value;
}

function report(e) {
 $("error").textContent = e.message || String(e);
}

function mine(p) {
 return p && (p === p.toUpperCase()) ===
        (state.player === "white");
}

function squares() {
 let files = [..."abcdefgh"];
 let ranks = [8,7,6,5,4,3,2,1];

 if(state.player === "black") {
  files.reverse();
  ranks.reverse();
 }
 return ranks.flatMap(r => files.map(f => f+r));
}

function render() {
 if(!state) return;

 $("color").value = state.player;
 $("turn").textContent =
  state.game_over ? "Game over" :
  state.turn === "white" ? "White to move" : "Black to move";

 $("status").textContent = state.result ||
  (state.turn === state.player
   ? "Stockfish is calculating..."
   : "Click the opponent's piece and destination.");

 const root = $("board");
 root.innerHTML = "";

 const names = squares();

 names.forEach((sq,i) => {
  const p = state.pieces[sq] || "";
  const el = document.createElement("button");

  el.className = "square " +
   ((Math.floor(i/8)+i%8)%2 === 0 ? "dark":"light");

  if(selected === sq) el.classList.add("selected");

  if(selected && state.legal.some(m =>
    m.from === selected && m.to === sq))
   el.classList.add("target");

  if(lastMove?.from === sq) el.classList.add("from");
  if(lastMove?.to === sq) el.classList.add("to");

  const piece = document.createElement("span");
  piece.className = "piece " +
   (p && p === p.toUpperCase()
     ? "whitepiece" : "blackpiece");
  piece.textContent = glyph[p] || "";
  el.appendChild(piece);

  if(i >= 56) {
   const label = document.createElement("span");
   label.className = "coord";
   label.textContent = sq[0];
   el.appendChild(label);
  }

  el.onclick = () => choose(sq);
  root.appendChild(el);
 });

 $("history").textContent = state.history.length
  ? state.history.map((m,i) =>
     (i%2===0 ? `${Math.floor(i/2)+1}. ` : "")+m
    ).join("   ")
  : "No moves yet.";

 $("fen").textContent = state.fen;
 $("promotion").style.display = pending ? "flex" : "none";
}

async function choose(sq) {
 if(!state || state.game_over ||
    state.turn === state.player || pending) return;

 const p = state.pieces[sq];

 if(selected) {
  const matching = state.legal.filter(m =>
   m.from === selected && m.to === sq);

  if(matching.length > 1) {
   pending = {from:selected,to:sq};
   render();
   return;
  }

  if(matching.length === 1) {
   try {
    await api("/api/move", {
     from:selected, to:sq
    });
    selected = null;
    $("error").textContent = "";
    await sync();
   } catch(e) { report(e); }
   return;
  }
 }

 selected = p && !mine(p) ? sq : null;
 render();
}

async function sync() {
 state = await api("/api/state");
 render();

 if(!state.game_over && state.turn === state.player) {
  await analyze();
 } else {
  lastMove = null;
  $("suggestion").textContent = "—";
  $("description").textContent =
   "Waiting for opponent's move";
  render();
 }
}

async function analyze() {
 const id = ++requestId;
 const fen = state.fen;

 $("suggestion").textContent = "Thinking...";
 $("description").textContent =
  "Stockfish is finding your move";

 try {
  const result = await api("/api/analyze", {
   fen:fen,
   time:Number($("think").value)
  });

  if(id !== requestId) return;

  const m = result.move;
  if(!m) return;

  lastMove = m;
  $("suggestion").textContent = m.san;
  $("description").textContent =
   `${m.from} → ${m.to} · Auto-played`;
  $("score").textContent =
   "Evaluation: " + result.score;

  // Automatically apply the Stockfish move.
  await api("/api/move", {
   from:m.from,
   to:m.to,
   promotion:m.promotion || "",
   fen:fen
  });

  if(id !== requestId) return;

  state = await api("/api/state");
  selected = null;
  $("error").textContent = "";
  render();

 } catch(e) {
  if(id === requestId) report(e);
 }
}

$("color").onchange = async () => {
 try {
  ++requestId;
  await api("/api/reset", {
   color:$("color").value
  });
  selected = null;
  pending = null;
  lastMove = null;
  await sync();
 } catch(e) { report(e); }
};

$("reset").onclick = async () => {
 if(!confirm("Start a new game?")) return;

 try {
  ++requestId;
  await api("/api/reset", {
   color:$("color").value
  });
  selected = null;
  pending = null;
  lastMove = null;
  await sync();
 } catch(e) { report(e); }
};

$("undo").onclick = async () => {
 try {
  ++requestId;
  await api("/api/undo", {});
  selected = null;
  pending = null;
  lastMove = null;
  await sync();
 } catch(e) { report(e); }
};

document.querySelectorAll("[data-promo]").forEach(btn => {
 btn.onclick = async () => {
  try {
   await api("/api/move", {
    ...pending,
    promotion:btn.dataset.promo
   });
   selected = null;
   pending = null;
   await sync();
  } catch(e) { report(e); }
 };
});

sync().catch(report);
</script>
</body>
</html>
"""

def get_state():
    legal = [
        {
            "from": chess.square_name(m.from_square),
            "to": chess.square_name(m.to_square),
            "promotion": chess.piece_symbol(m.promotion)
                         if m.promotion else ""
        }
        for m in board.legal_moves
    ]

    replay = chess.Board()
    history = []
    for m in board.move_stack:
        history.append(replay.san(m))
        replay.push(m)

    outcome = board.outcome(claim_draw=True)

    return {
        "player": "white" if player else "black",
        "turn": "white" if board.turn else "black",
        "pieces": {
            chess.square_name(s): p.symbol()
            for s,p in board.piece_map().items()
        },
        "legal": legal,
        "history": history,
        "fen": board.fen(),
        "game_over": outcome is not None,
        "result": outcome.result() if outcome else ""
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def respond(self, data, code=200):
        raw = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/":
            raw = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        elif self.path == "/api/state":
            with lock:
                self.respond(get_state())
        else:
            self.respond({"error":"Not found"},404)

    def do_POST(self):
        global board,player

        try:
            size = int(self.headers.get("Content-Length","0"))
            if size > 4096:
                raise ValueError("Request too large")

            data = json.loads(self.rfile.read(size) or b"{}")

            with lock:
                if self.path == "/api/reset":
                    color = data.get("color")
                    if color not in ("white","black"):
                        raise ValueError("Invalid color")

                    player = color == "white"
                    board.reset()
                    self.respond(get_state())

                elif self.path == "/api/undo":
                    if board.move_stack:
                        board.pop()
                    self.respond(get_state())

                elif self.path == "/api/move":
                    if data.get("fen") and data["fen"] != board.fen():
                        raise ValueError("Position changed")

                    src = chess.parse_square(data["from"])
                    dst = chess.parse_square(data["to"])
                    promotion = data.get("promotion","")

                    prom = (
                        chess.PIECE_SYMBOLS.index(promotion)
                        if promotion else None
                    )

                    move = chess.Move(src,dst,promotion=prom)

                    if move not in board.legal_moves:
                        raise ValueError("Illegal move")

                    board.push(move)
                    self.respond(get_state())

                elif self.path == "/api/analyze":
                    if board.is_game_over(claim_draw=True):
                        self.respond({
                            "move":None,
                            "score":"Game over"
                        })
                        return

                    if board.turn != player:
                        raise ValueError("Opponent's turn")

                    if data.get("fen") != board.fen():
                        raise ValueError("Position changed")

                    seconds = max(
                        0.1,
                        min(5.0,float(data.get("time",0.5)))
                    )

                    info = engine.analyse(
                        board,
                        chess.engine.Limit(time=seconds)
                    )

                    move = info["pv"][0]
                    score = info["score"].pov(player)

                    if score.is_mate():
                        text = f"Mate in {score.mate()}"
                    else:
                        text = f"{score.score()/100:+.2f} pawns"

                    self.respond({
                        "move": {
                            "from":chess.square_name(move.from_square),
                            "to":chess.square_name(move.to_square),
                            "promotion":(
                                chess.piece_symbol(move.promotion)
                                if move.promotion else ""
                            ),
                            "san":board.san(move)
                        },
                        "score":text
                    })

                else:
                    self.respond({"error":"Not found"},404)

        except (ValueError,KeyError,TypeError) as e:
            self.respond({"error":str(e)},400)
        except Exception as e:
            self.respond({"error":str(e)},500)


def main():
    global engine

    engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    server = ThreadingHTTPServer((HOST,PORT),Handler)

    url = f"http://{HOST}:{PORT}"
    print("Chess Advisor:",url)
    print("Press Ctrl+C to stop.")

    threading.Timer(0.6,lambda:webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        engine.quit()


if __name__ == "__main__":
    main()

