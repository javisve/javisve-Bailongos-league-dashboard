import os
import sys
import json
import time
import requests
from datetime import datetime, timezone

BASE_URL = "https://biwenger.as.com/api/v2"
CDN_URL = "https://cf.biwenger.com/api/v2"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_JSON_PATH = os.path.join(SCRIPT_DIR, "data.json")
DATA_JS_PATH = os.path.join(SCRIPT_DIR, "data.js")
CACHE_FILE = os.path.join(SCRIPT_DIR, "competitions_cache.json")

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def load_credentials():
    email = os.environ.get("BIWENGER_EMAIL") or os.environ.get("BIWENGER_USER")
    pwd = os.environ.get("BIWENGER_PASSWORD")
    if email and pwd:
        return {"user": email, "password": pwd}

    candidates = ["password.txt", os.path.join(SCRIPT_DIR, "password.txt"), os.path.join(os.path.dirname(SCRIPT_DIR), "password.txt")]
    for p in candidates:
        if os.path.exists(p):
            creds = {}
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        k, v = line.strip().split(":", 1)
                        creds[k.strip()] = v.strip()
            if creds.get("user") and creds.get("password"):
                return creds
    return {}

def login(email, password):
    url = f"{BASE_URL}/auth/login"
    resp = requests.post(url, json={"email": email, "password": password}, headers={"Content-Type": "application/json"}, timeout=15)
    if resp.status_code == 200:
        return resp.json().get("token")
    raise Exception(f"Login fallido ({resp.status_code}): {resp.text}")

def get_headers(token, league_id=None, user_id=None):
    h = {
        "Authorization": f"Bearer {token}",
        "X-Version": "631",
        "X-Lang": "es"
    }
    if league_id:
        h["X-League"] = str(league_id)
    if user_id:
        h["X-User"] = str(user_id)
    return h

def get_competition_data():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://biwenger.as.com/"
    }
    url = f"{CDN_URL}/competitions/la-liga/data?lang=es&score=5"
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data and "players" in data["data"]:
                    with open(CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False)
                    return data.get("data", {})
        except Exception as e:
            log(f"Reintento {attempt+1} descargando datos de LaLiga: {e}")
            time.sleep(1)

    parent_cache = os.path.join(os.path.dirname(SCRIPT_DIR), "competitions_cache.json")
    for c_path in [CACHE_FILE, parent_cache]:
        if os.path.exists(c_path):
            with open(c_path, "r", encoding="utf-8") as f:
                return json.load(f).get("data", {})
    return {"players": {}, "teams": {}}

def fetch_all_board_events(headers, league_id):
    all_events = []
    offset = 0
    while True:
        url = f"{BASE_URL}/league/{league_id}/board?offset={offset}&limit=100"
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            break
        data = resp.json().get("data", [])
        if not data:
            break
        all_events.extend(data)
        if len(data) < 100:
            break
        offset += len(data)
    return all_events

def build_dream_team(all_league_players):
    gks = [p for p in all_league_players if p["positionId"] == 1]
    dfs = [p for p in all_league_players if p["positionId"] == 2]
    mfs = [p for p in all_league_players if p["positionId"] == 3]
    fws = [p for p in all_league_players if p["positionId"] == 4]

    gks.sort(key=lambda x: (x["points"], x["price"]), reverse=True)
    dfs.sort(key=lambda x: (x["points"], x["price"]), reverse=True)
    mfs.sort(key=lambda x: (x["points"], x["price"]), reverse=True)
    fws.sort(key=lambda x: (x["points"], x["price"]), reverse=True)

    schemas = [
        {"name": "3-4-3", "gk": 1, "df": 3, "mc": 4, "dl": 3},
        {"name": "3-5-2", "gk": 1, "df": 3, "mc": 5, "dl": 2},
        {"name": "4-3-3", "gk": 1, "df": 4, "mc": 3, "dl": 3},
        {"name": "4-4-2", "gk": 1, "df": 4, "mc": 4, "dl": 2},
        {"name": "4-5-1", "gk": 1, "df": 4, "mc": 5, "dl": 1},
    ]

    best_formation = None
    best_points = -1
    best_lineup = []

    for sch in schemas:
        if len(gks) >= sch["gk"] and len(dfs) >= sch["df"] and len(mfs) >= sch["mc"] and len(fws) >= sch["dl"]:
            chosen = gks[:sch["gk"]] + dfs[:sch["df"]] + mfs[:sch["mc"]] + fws[:sch["dl"]]
            total_pts = sum(p["points"] for p in chosen)
            if total_pts > best_points:
                best_points = total_pts
                best_formation = sch["name"]
                best_lineup = chosen

    if not best_lineup:
        all_sorted = sorted(all_league_players, key=lambda x: (x["points"], x["price"]), reverse=True)
        best_lineup = all_sorted[:11]
        best_formation = "3-4-3"

    return {
        "formation": best_formation,
        "totalPoints": sum(p["points"] for p in best_lineup),
        "totalValue": sum(p["price"] for p in best_lineup),
        "players": best_lineup
    }

def main():
    log("Iniciando extraccion de datos publicos y curiosidades...")
    creds = load_credentials()
    if not creds.get("user") or not creds.get("password"):
        log("ERROR: No se encontraron credenciales")
        sys.exit(1)

    token = login(creds["user"], creds["password"])
    acc = requests.get(f"{BASE_URL}/account", headers=get_headers(token)).json()
    leagues = acc.get("data", {}).get("leagues", [])
    if not leagues:
        log("ERROR: No se encontraron ligas en la cuenta.")
        sys.exit(1)

    main_league = leagues[0]
    league_id = main_league.get("id")
    my_user_id = main_league.get("user", {}).get("id")
    headers = get_headers(token, league_id, my_user_id)
    league_name = main_league.get("name", "Liga Biwenger")

    log(f"Conectado a la liga '{league_name}' (ID: {league_id})")

    comp_data = get_competition_data()
    all_players_db = comp_data.get("players", {})
    all_teams_db = comp_data.get("teams", {})

    pos_names = {1: "Portero", 2: "Defensa", 3: "Centrocampista", 4: "Delantero"}
    pos_shorts = {1: "PT", 2: "DF", 3: "MC", 4: "DL"}

    req_url = f"{BASE_URL}/league?fields=*,users(id,name,icon,players(id,owner)),standings"
    league_info = requests.get(req_url, headers=headers, timeout=15).json().get("data", {})

    users_raw = league_info.get("users", [])
    standings_raw = league_info.get("standings", [])
    standings_map = {s["id"]: s for s in standings_raw}

    board_events = fetch_all_board_events(headers, league_id)
    log(f"Descargados {len(board_events)} eventos del tablon.")

    transfers_count = {u["id"]: 0 for u in users_raw}
    for ev in board_events:
        etype = ev.get("type")
        content = ev.get("content", [])
        if etype in ["market", "transfer"] and isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    fid = item.get("from", {}).get("id") if isinstance(item.get("from"), dict) else item.get("from")
                    tid = item.get("to", {}).get("id") if isinstance(item.get("to"), dict) else item.get("to")
                    if fid in transfers_count:
                        transfers_count[fid] += 1
                    if tid in transfers_count:
                        transfers_count[tid] += 1

    managers_data = []
    all_league_players = []

    for u in users_raw:
        uid = u["id"]
        uname = u["name"]
        uicon = u.get("icon", "")
        standing = standings_map.get(uid, {})
        points_total = standing.get("points", 0)
        position = standing.get("position", len(managers_data) + 1)

        raw_players = u.get("players", [])
        processed_players = []
        total_squad_value = 0
        team_counts = {}

        for p in raw_players:
            pid = p["id"]
            owner_info = p.get("owner", {})
            p_info = all_players_db.get(str(pid), {})

            pname = p_info.get("name", f"Jugador {pid}")
            slug = p_info.get("slug", "")
            team_id = p_info.get("teamID")
            team_name = all_teams_db.get(str(team_id), {}).get("name", "Desconocido")
            pos_id = p_info.get("position", 0)
            price = p_info.get("price", 0)
            price_inc = p_info.get("priceIncrement", 0)
            pts = p_info.get("points", 0)
            status = p_info.get("status", "ok")
            status_info = p_info.get("statusInfo")
            fitness = p_info.get("fitness", [])
            purchase_price = owner_info.get("price", price)
            purchase_date = owner_info.get("date")

            total_squad_value += price

            if team_name and team_name != "Desconocido":
                team_counts[team_name] = team_counts.get(team_name, 0) + 1

            pts_per_million = round((pts / (price / 1_000_000)), 2) if price > 0 else 0

            negative_matches = 0
            if isinstance(fitness, list):
                for f_val in fitness:
                    if isinstance(f_val, (int, float)) and f_val < 0:
                        negative_matches += 1

            player_obj = {
                "id": pid,
                "name": pname,
                "slug": slug,
                "photoUrl": f"https://cdn.biwenger.com/i/p/{pid}.png",
                "teamId": team_id,
                "teamName": team_name,
                "positionId": pos_id,
                "positionName": pos_names.get(pos_id, "Otro"),
                "positionShort": pos_shorts.get(pos_id, "OT"),
                "price": price,
                "priceIncrement": price_inc,
                "purchasePrice": purchase_price,
                "purchaseDate": purchase_date,
                "points": pts,
                "fitness": fitness,
                "status": status,
                "statusInfo": status_info,
                "ptsPerMillion": pts_per_million,
                "negativeMatches": negative_matches,
                "ownerId": uid,
                "ownerName": uname
            }

            processed_players.append(player_obj)
            all_league_players.append(player_obj)

        max_club_name = "-"
        max_club_count = 0
        for cname, count in team_counts.items():
            if count > max_club_count:
                max_club_count = count
                max_club_name = cname

        avg_pts_per_player = round(points_total / len(processed_players), 2) if processed_players else 0

        if uicon.startswith("http"):
            icon_url = uicon
        elif uicon:
            icon_url = f"https://cdn.biwenger.com/{uicon}"
        else:
            icon_url = ""

        manager_obj = {
            "id": uid,
            "name": uname,
            "icon": icon_url,
            "position": position,
            "points": points_total,
            "squadValue": total_squad_value,
            "playerCount": len(processed_players),
            "avgPointsPerPlayer": avg_pts_per_player,
            "transfersCount": transfers_count.get(uid, 0),
            "dominantClub": {"name": max_club_name, "count": max_club_count},
            "players": processed_players
        }
        managers_data.append(manager_obj)

    managers_data.sort(key=lambda x: (x["points"], -x["position"]), reverse=True)
    for idx, m in enumerate(managers_data):
        m["position"] = idx + 1

    # Calculos de Trofeos
    rey_midas = max(managers_data, key=lambda m: m["squadValue"]) if managers_data else None
    el_austero = min(managers_data, key=lambda m: m["squadValue"]) if managers_data else None
    maquina_fichar = max(managers_data, key=lambda m: m["transfersCount"]) if managers_data else None
    monotematico = max(managers_data, key=lambda m: m["dominantClub"]["count"]) if managers_data else None

    candidates_chollo = [p for p in all_league_players if p["points"] > 0 and p["price"] > 0]
    if candidates_chollo:
        el_chollo = max(candidates_chollo, key=lambda p: (p["ptsPerMillion"], p["points"]))
    else:
        el_chollo = min(all_league_players, key=lambda p: p["price"]) if all_league_players else None

    expensive_players = sorted(all_league_players, key=lambda p: p["price"], reverse=True)
    if expensive_players:
        top_slice = expensive_players[:min(25, len(expensive_players))]
        el_pozo = min(top_slice, key=lambda p: (p["points"], -p["price"]))
    else:
        el_pozo = None

    masterclass = max(managers_data, key=lambda m: m["points"]) if managers_data else None
    jornada_negra = min(managers_data, key=lambda m: m["points"]) if managers_data else None
    el_inmovilista = min(managers_data, key=lambda m: m["transfersCount"]) if managers_data else None

    best_talisman = max(all_league_players, key=lambda p: (p["points"], p["price"])) if all_league_players else None
    capitan_general = None
    if best_talisman:
        capitan_general = {
            "manager": next((m for m in managers_data if m["id"] == best_talisman["ownerId"]), None),
            "player": best_talisman
        }

    # Tops especificos
    top5_expensive = sorted(all_league_players, key=lambda p: p["price"], reverse=True)[:5]
    top5_points = sorted(all_league_players, key=lambda p: (p["points"], p["price"]), reverse=True)[:5]

    # Top 5 por pts/M€ (mejor rentabilidad)
    valid_ppm_candidates = [p for p in all_league_players if p["points"] > 0 and p["price"] > 0]
    top5_pts_per_million = sorted(valid_ppm_candidates, key=lambda p: (p["ptsPerMillion"], p["points"]), reverse=True)[:5]

    # Top 5 Pufos (peores jugadores por pts/M€)
    top5_pufos = sorted([p for p in all_league_players if p.get("price", 0) > 0], key=lambda p: (p["ptsPerMillion"], p["points"], -p["price"]))[:5]

    dream_team = build_dream_team(all_league_players)

    dashboard_payload = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "league": {
            "id": league_id,
            "name": league_name,
            "totalManagers": len(managers_data),
            "totalPlayersOwned": len(all_league_players),
            "totalMarketValue": sum(m["squadValue"] for m in managers_data)
        },
        "standings": managers_data,
        "trophies": {
            "laMasterclass": {
                "title": "La Masterclass",
                "badge": "💥",
                "description": "Mayor puntuación registrada en la liga",
                "manager": masterclass["name"] if masterclass else "-",
                "value": f"{masterclass['points']} pts" if masterclass else "-"
            },
            "jornadaNegra": {
                "title": "La Jornada Negra",
                "badge": "🧱",
                "description": "Puntuación más baja registrada en la liga",
                "manager": jornada_negra["name"] if jornada_negra else "-",
                "value": f"{jornada_negra['points']} pts" if jornada_negra else "-"
            },
            "balonDeOro": {
                "title": "Balón de Oro",
                "badge": "⭐",
                "description": "Mejor jugador de la liga",
                "manager": capitan_general["manager"]["name"] if capitan_general and capitan_general["manager"] else "-",
                "player": capitan_general["player"]["name"] if capitan_general and capitan_general["player"] else "-",
                "value": f"{capitan_general['player']['points']} pts" if capitan_general and capitan_general["player"] else "-"
            },
            "maquinaFichar": {
                "title": "La Máquina de Fichar",
                "badge": "🚜",
                "description": "Mánager que más fichajes ha cerrado en el mercado",
                "manager": maquina_fichar["name"] if maquina_fichar else "-",
                "value": f"{maquina_fichar['transfersCount']} fichajes" if maquina_fichar else "-"
            },
            "elInmovilista": {
                "title": "El Inmovilista",
                "badge": "🗿",
                "description": "Mánager más fiel a su equipo (menos fichajes en el mercado)",
                "manager": el_inmovilista["name"] if el_inmovilista else "-",
                "value": f"{el_inmovilista['transfersCount']} fichajes" if el_inmovilista else "-"
            },
            "reyMidas": {
                "title": "El Rey Midas",
                "badge": "💎",
                "description": "Mánager con la plantilla más cotizada de la liga",
                "manager": rey_midas["name"] if rey_midas else "-",
                "value": f"{rey_midas['squadValue']:,} €".replace(",", ".") if rey_midas else "-"
            },
            "elMonje": {
                "title": "El Monje / Austero",
                "badge": "🪙",
                "description": "Mánager con el equipo más humilde en valor",
                "manager": el_austero["name"] if el_austero else "-",
                "value": f"{el_austero['squadValue']:,} €".replace(",", ".") if el_austero else "-"
            },
            "elChollo": {
                "title": "El Chollo de la Liga",
                "badge": "🏷️",
                "description": "Jugador de bajo coste y gran rendimiento en puntos",
                "player": el_chollo["name"] if el_chollo else "-",
                "owner": el_chollo["ownerName"] if el_chollo else "-",
                "value": f"{el_chollo['points']} pts / {el_chollo['price']:,} €".replace(",", ".") if el_chollo else "-"
            },
            "elPozo": {
                "title": "El Pozo sin Fondo",
                "badge": "💸",
                "description": "Jugador de alto coste y bajo rendimiento en puntos",
                "player": el_pozo["name"] if el_pozo else "-",
                "owner": el_pozo["ownerName"] if el_pozo else "-",
                "value": f"{el_pozo['points']} pts / {el_pozo['price']:,} €".replace(",", ".") if el_pozo else "-"
            },
            "elMonotematico": {
                "title": "El Monotemático",
                "badge": "🏟️",
                "description": "Mánager con más jugadores del mismo club de LaLiga",
                "manager": monotematico["name"] if monotematico else "-",
                "value": f"{monotematico['dominantClub']['count']} jugadores ({monotematico['dominantClub']['name']})" if monotematico else "-"
            }
        },
        "top5Expensive": top5_expensive,
        "top5Points": top5_points,
        "top5PtsPerMillion": top5_pts_per_million,
        "top5Pufos": top5_pufos,
        "dreamTeam": dream_team
    }

    with open(DATA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(dashboard_payload, f, ensure_ascii=False, indent=2)

    with open(DATA_JS_PATH, "w", encoding="utf-8") as f:
        f.write(f"window.BIWENGER_COMMUNITY_DATA = {json.dumps(dashboard_payload, ensure_ascii=False, indent=2)};")

    log(f"Exito! Datos exportados correctamente en '{DATA_JSON_PATH}' y '{DATA_JS_PATH}'.")

if __name__ == "__main__":
    main()
