import csv
import os
import re
import ast
from statistics import median, quantiles


TEAM_ABBREVIATIONS = {
    'Paper Rex': 'PRX',
    'Xi Lai Gaming': 'XLG', 
    'GIANTX': 'GX',
    'Sentinels': 'SEN',
    'NRG': 'NRG',
    'EDward Gaming': 'EDG',
    'Team Liquid': 'TL',
    'DRX': 'DRX',
    'Dragon Ranger Gaming': 'DRG',
    'T1': 'T1',
    'G2 Esports': 'G2',
    'Team Heretics': 'TH',
    'Bilibili Gaming': 'BLG',
    'MIBR': 'MIBR',
    'Rex Regum Qeon': 'RRQ',
    'FNATIC': 'FNC',
    'Guangzhou Huadu Bilibili Gaming(Bilibili Gaming)': 'BLG', 
    'PRX': 'PRX', 'XLG': 'XLG', 'GX': 'GX', 'SEN': 'SEN', 'NRG': 'NRG', 'EDG': 'EDG', 'TL': 'TL',
    'DRX': 'DRX', 'DRG': 'DRG', 'T1': 'T1', 'G2': 'G2', 'TH': 'TH', 'BLG': 'BLG', 'MIBR': 'MIBR',
    'RRQ': 'RRQ', 'FNC': 'FNC'
}

def get_team_abbr(team_name: str, mapping=TEAM_ABBREVIATIONS) -> str:
    name = team_name.strip()
    return mapping.get(name, name)


def resolver_caminho(file_name: str) -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    path_root = os.path.join(here, file_name)
    path_data = os.path.join(here, 'data', file_name)
    if os.path.exists(path_root):
        return path_root
    if os.path.exists(path_data):
        return path_data
    return path_root


def ler_csv_dicts(file_name: str):
    path = resolver_caminho(file_name)
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def parsear_porcentagem(value: str) -> float:
    if value is None:
        return 0.0
    s = str(value).strip().replace(',', '.')
    if s.endswith('%'):
        s = s[:-1]
    try:
        return float(s)
    except ValueError:
        return 0.0


def parsear_float(value: str) -> float:
    if value is None:
        return 0.0
    s = str(value).strip().replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0


def parsear_int(value: str) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def parsear_tupla_vitorias(text: str):
    if text is None:
        return 0, 0
    m = re.match(r"\s*(\d+)\s*\((\d+)\)\s*", str(text))
    if not m:
        n = parsear_int(text)
        return n, 0
    total = int(m.group(1))
    wins = int(m.group(2))
    return total, wins


def carregar_stats_jogadores():
    return ler_csv_dicts('player_stats.csv')


def carregar_stats_agentes():
    return ler_csv_dicts('agents_stats.csv')


def carregar_stats_mapas():
    return ler_csv_dicts('maps_stats.csv')


def carregar_dados_economia():
    return ler_csv_dicts('economy_data.csv')


def carregar_dados_performance():
    return ler_csv_dicts('performance_data.csv')


def carregar_partidas_detalhadas():
    return ler_csv_dicts('detailed_matches_maps.csv')


def fazer_tabela(headers, rows):
    if not headers or not rows:
        return
    
    headers = [str(h) for h in headers]
    rows = [[str(cell) for cell in row] for row in rows]
    
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(header)
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(row[i]))
        col_widths.append(max_width + 2)
    
    def fazer_linha():
        return "+" + "+".join("-" * width for width in col_widths) + "+"
    
    def fazer_row(cells):
        row_parts = []
        for i, cell in enumerate(cells):
            if i < len(col_widths):
                padded_cell = cell.ljust(col_widths[i] - 1)
                row_parts.append(padded_cell)
        return "|" + "|".join(row_parts) + "|"
    
    print(fazer_linha())
    print(fazer_row(headers))
    print(fazer_linha())
    for row in rows:
        print(fazer_row(row))
    print(fazer_linha())


def listar_top10_performance():
    players = carregar_stats_jogadores()
    for p in players:
        p['rating_num'] = parsear_float(p.get('rating'))
        p['acs_num'] = parsear_float(p.get('acs'))
        p['kast_num'] = parsear_porcentagem(p.get('kast'))
    players.sort(key=lambda p: (p['rating_num'], p['acs_num'], p['kast_num']), reverse=True)
    headers = ["Rank", "Jogador", "Time", "Rating", "ACS", "KAST"]
    rows = []
    for i, p in enumerate(players[:10], start=1):
        rows.append([
            i,
            p.get('player_name','?'),
            p.get('team','?'),
            f"{p['rating_num']:.2f}",
            f"{p['acs_num']:.1f}",
            f"{p['kast_num']:.0f}%",
        ])
    fazer_tabela(headers, rows)


def top_5_especialistas():
    players = carregar_stats_jogadores()
    agente_escolhido = input("Agente: ").strip()
    alvo = (agente_escolhido or '').strip().lower()
    candidatos = []
    for p in players:
        agents_field = p.get('agents')
        try:
            agent_list = ast.literal_eval(agents_field) if agents_field else []
        except Exception:
            agent_list = []
        agent_list_lower = [str(a).lower() for a in agent_list]
        if alvo and alvo in agent_list_lower:
            p['kast_num'] = parsear_porcentagem(p.get('kast'))
            p['rating_num'] = parsear_float(p.get('rating'))
            p['acs_num'] = parsear_float(p.get('acs'))
            candidatos.append(p)

    if not candidatos:
        print(f"Nenhum jogador encontrado que jogue o agente '{agente_escolhido}'.")
        return

    candidatos.sort(key=lambda p: (p['kast_num'], p['rating_num'], p['acs_num']), reverse=True)
    headers = ["Rank", "Jogador", "Time", "KAST", "Rating", "ACS"]
    rows = []
    for i, p in enumerate(candidatos[:5], start=1):
        rows.append([
            i,
            p.get('player_name','?'),
            p.get('team','?'),
            f"{parsear_porcentagem(p.get('kast')):.0f}%",
            f"{parsear_float(p.get('rating')):.2f}",
            f"{parsear_float(p.get('acs')):.1f}",
        ])
    fazer_tabela(headers, rows)


def pickrate_por_mapa():
    stats = carregar_stats_agentes()
    mapa_escolhido = input("Mapa: ").strip()
    mapa_col = (mapa_escolhido or '').strip()
    if not mapa_col:
        print("Mapa não informado.")
        return
    mapa_norm = mapa_col.strip()

    if not stats or mapa_norm not in stats[0]:
        disponiveis = [k for k in (stats[0].keys() if stats else []) if k.lower() not in {'agent_name', 'total_utilization'}]
        print(f"Mapa '{mapa_escolhido}' não encontrado. Mapas disponíveis: {', '.join(disponiveis)}")
        return

    linhas = []
    for row in stats:
        agent = row.get('agent_name')
        pick = parsear_float(row.get(mapa_norm))
        linhas.append((agent, pick))
    linhas.sort(key=lambda x: x[1], reverse=True)

    headers = [f"Agente ({mapa_norm})", "Pickrate"]
    rows = [[agent, f"{pick:.1f}%"] for agent, pick in linhas]
    fazer_tabela(headers, rows)
    print("Winrate por agente no mapa: N/D (não disponível nos dados fornecidos)")


def comparar_economia_times():
    time_a = input("Time A: ").strip()
    time_b = input("Time B: ").strip()

    team_a_abbr = get_team_abbr(time_a)
    team_b_abbr = get_team_abbr(time_b)
    
    econ = carregar_dados_economia()
    def acumular(team_abbr: str):
        filtro = [r for r in econ if str(r.get('Team','')).strip().upper() == team_abbr.upper()]
        total = {
            'pistol_won': 0,
            'eco_total': 0, 'eco_wins': 0,
            'semi_eco_total': 0, 'semi_eco_wins': 0,
            'semi_buy_total': 0, 'semi_buy_wins': 0,
            'full_buy_total': 0, 'full_buy_wins': 0,
        }
        for r in filtro:
            total['pistol_won'] += parsear_int(r.get('Pistol Won'))
            t, w = parsear_tupla_vitorias(r.get('Eco (won)'))
            total['eco_total'] += t; total['eco_wins'] += w
            t, w = parsear_tupla_vitorias(r.get('Semi-eco (won)'))
            total['semi_eco_total'] += t; total['semi_eco_wins'] += w
            t, w = parsear_tupla_vitorias(r.get('Semi-buy (won)'))
            total['semi_buy_total'] += t; total['semi_buy_wins'] += w
            t, w = parsear_tupla_vitorias(r.get('Full buy(won)'))
            total['full_buy_total'] += t; total['full_buy_wins'] += w
        return total

    def ratio(wins: int, total: int) -> float:
        return (wins / total * 100.0) if total > 0 else 0.0

    a = acumular(team_a_abbr)
    b = acumular(team_b_abbr)

    headers = ["Métrica", time_a, time_b]
    rows = [
        ["Pistol won", a['pistol_won'], b['pistol_won']],
        ["Eco win%", f"{ratio(a['eco_wins'], a['eco_total']):.1f}%", f"{ratio(b['eco_wins'], b['eco_total']):.1f}%"],
        ["Semi-eco win%", f"{ratio(a['semi_eco_wins'], a['semi_eco_total']):.1f}%", f"{ratio(b['semi_eco_wins'], b['semi_eco_total']):.1f}%"],
        ["Semi-buy win%", f"{ratio(a['semi_buy_wins'], a['semi_buy_total']):.1f}%", f"{ratio(b['semi_buy_wins'], b['semi_buy_total']):.1f}%"],
        ["Full-buy win%", f"{ratio(a['full_buy_wins'], a['full_buy_total']):.1f}%", f"{ratio(b['full_buy_wins'], b['full_buy_total']):.1f}%"],
    ]
    fazer_tabela(headers, rows)


def jogadores_adaptativos():
    players = carregar_stats_jogadores()
    fk_list = []
    cl_list = []
    for p in players:
        fk_list.append(parsear_int(p.get('first_kills')))
        cl_list.append(parsear_porcentagem(p.get('cl_percent')))

    if not players:
        print("Sem dados de jogadores")
        return

    try:
        q_fk = quantiles(fk_list, n=4)[2]
        q_cl = quantiles(cl_list, n=4)[2]
    except Exception:
        q_fk = median(fk_list)
        q_cl = median(cl_list)

    altos_fk = {p.get('player_name') for p in players if parsear_int(p.get('first_kills')) >= q_fk}
    altos_cl = {p.get('player_name') for p in players if parsear_porcentagem(p.get('cl_percent')) >= q_cl}
    intersec = [p for p in players if p.get('player_name') in altos_fk and p.get('player_name') in altos_cl]

    headers = ["Jogador", "Time", "First Kills", "Clutch%"]
    rows = []
    for p in intersec:
        rows.append([
            p.get('player_name','?'),
            p.get('team','?'),
            parsear_int(p.get('first_kills')),
            f"{parsear_porcentagem(p.get('cl_percent')):.0f}%",
        ])
    fazer_tabela(headers, rows)


def analisar_winrate_pick():
    time_escolhido = input("Time: ").strip()
    time = (time_escolhido or '').strip()
    time = get_team_abbr(time) #vsfffffffffff
    if not time:
        print("Equipe invalida.")
        return
    
    overview = ler_csv_dicts('detailed_matches_overview.csv')
    team_matches = {}
    for match in overview:
        if time in match['teams']:
            teams = match['teams'].split(' vs ')
            opponent = teams[1] if teams[0] == time else teams[0]
            team_matches[match['match_id']] = {
                'opponent': opponent,
                'score': match['score'],
                'date': match['date']
            }
    
    if not team_matches:
        print(f"Time '{time}' não encontrado nos dados.")
        return
    
    rows = carregar_partidas_detalhadas()
    contagem = {
        'proprio_pick': {'wins': 0, 'total': 0, 'details': []},
        'pick_adversario': {'wins': 0, 'total': 0, 'details': []},
        'decider': {'wins': 0, 'total': 0, 'details': []},
    }

    for r in rows:
        match_id = r.get('match_id')
        if match_id not in team_matches:
            continue
            
        picked_by = str(r.get('picked_by','')).strip()
        winner = str(r.get('winner','')).strip()
        map_name = r.get('map_name', '')
        score = r.get('score', '')
        
        if picked_by.lower() == 'decider':
            cat = 'decider'
        elif picked_by.lower() == time.lower():
            cat = 'proprio_pick'
        else:
            cat = 'pick_adversario'

        contagem[cat]['total'] += 1
        won = winner.lower() == time.lower()
        if won:
            contagem[cat]['wins'] += 1
        
        match_info = team_matches[match_id]
        result = "V" if won else "D"
        contagem[cat]['details'].append({
            'map': map_name,
            'opponent': match_info['opponent'],
            'score': score,
            'result': result,
            'picked_by': picked_by
        })

    def rate(c):
        return (contagem[c]['wins'] / contagem[c]['total'] * 100.0) if contagem[c]['total'] > 0 else 0.0

    headers = ["Cenário", "Wins", "Total", "Win%"]
    label_map = {
        'proprio_pick': 'Próprio Pick',
        'pick_adversario': 'Pick do Adversário',
        'decider': 'Decider',
    }
    rows = []
    for key in ['proprio_pick', 'pick_adversario', 'decider']:
        rows.append([
            label_map[key],
            contagem[key]['wins'],
            contagem[key]['total'],
            f"{rate(key):.1f}%",
        ])
    fazer_tabela(headers, rows)
    
    print(f"\n=== DETALHES DOS MAPAS PARA {time} ===")
    for key in ['proprio_pick', 'pick_adversario', 'decider']:
        if contagem[key]['total'] > 0:
            print(f"\n{label_map[key]} ({contagem[key]['wins']}/{contagem[key]['total']} - {rate(key):.1f}%):")
            details_headers = ["Mapa", "Adversário", "Score", "Resultado", "Pick"]
            details_rows = []
            for detail in contagem[key]['details']:
                details_rows.append([
                    detail['map'],
                    detail['opponent'],
                    detail['score'],
                    detail['result'],
                    detail['picked_by']
                ])
            fazer_tabela(details_headers, details_rows)


def ranking_final_times():
    official_ranking = [
        {"pos": "1º Lugar", "team": "NRG", "stage": "Vencedor da Grande Final"},
        {"pos": "2º Lugar", "team": "FNATIC", "stage": "Perdeu a Grande Final para NRG (3-2)"},
        {"pos": "3º Lugar", "team": "DRX", "stage": "Perdeu a Final Inferior (Lower Final) para FNATIC (3-1)"},
        {"pos": "4º Lugar", "team": "Paper Rex", "stage": "Eliminado na Rodada 3 Inferior (Lower Round 3) por DRX (2-0)"},
        {"pos": "5º-6º Lugares", "team": "MIBR", "stage": "Eliminado na Rodada 2 Inferior (Lower Round 2) por DRX (2-1)"},
        {"pos": "", "team": "Team Heretics", "stage": "Eliminado na Rodada 2 Inferior (Lower Round 2) por Paper Rex (2-1)"},
        {"pos": "7º-8º Lugares", "team": "G2 Esports", "stage": "Eliminado na Rodada 1 Inferior (Lower Round 1) por DRX (2-1)"},
        {"pos": "", "team": "GIANTX", "stage": "Eliminado na Rodada 1 Inferior (Lower Round 1) por Team Heretics (2-1)"},
        {"pos": "9º-12º Lugares", "team": "Team Liquid", "stage": "Eliminado na Fase de Grupos (Decider C) por DRX (2-0)"},
        {"pos": "", "team": "Xi Lai Gaming", "stage": "Eliminado na Fase de Grupos (Decider A) por GIANTX (2-0)"},
        {"pos": "", "team": "T1", "stage": "Eliminado na Fase de Grupos (Decider D) por G2 Esports (2-0)"},
        {"pos": "", "team": "Rex Regum Qeon", "stage": "Eliminado na Fase de Grupos (Decider B) por MIBR (2-0)"},
        {"pos": "13º-16º Lugares", "team": "Sentinels", "stage": "Eliminado na Fase de Grupos (Elimination A) por Xi Lai Gaming (2-1)"},
        {"pos": "", "team": "EDward Gaming", "stage": "Eliminado na Fase de Grupos (Elimination C) por Team Liquid (2-1)"},
        {"pos": "", "team": "Bilibili Gaming", "stage": "Eliminado na Fase de Grupos (Elimination B) por Rex Regum Qeon (2-1)"},
        {"pos": "", "team": "Dragon Ranger Gaming", "stage": "Eliminado na Fase de Grupos (Elimination D) por G2 Esports (2-0)"},
    ]
    
    overview = ler_csv_dicts('detailed_matches_overview.csv')
    maps_rows = carregar_partidas_detalhadas()
    player_rows = carregar_stats_jogadores()
    
    team_stats = {}
    for entry in official_ranking:
        team = entry['team']
        team_stats[team] = {
            'series_wins': 0,
            'series_losses': 0,
            'maps_wins': 0,
            'maps_losses': 0,
            'rating': 0.0,
            'acs': 0.0,
            'kast': 0.0,
            'player_count': 0
        }
    
    for m in overview:
        mid = m['match_id']
        t1, t2 = [t.strip() for t in m['teams'].split(' vs ')]
        if t1 in team_stats and t2 in team_stats:
            w_counts = {t1: 0, t2: 0}
            for r in maps_rows:
                if r['match_id'] == mid:
                    w_counts[r['winner']] = w_counts.get(r['winner'], 0) + 1
            if w_counts[t1] > w_counts[t2]:
                team_stats[t1]['series_wins'] += 1
                team_stats[t2]['series_losses'] += 1
            else:
                team_stats[t2]['series_wins'] += 1
                team_stats[t1]['series_losses'] += 1
    
    for r in maps_rows:
        winner = r['winner']
        if winner in team_stats:
            team_stats[winner]['maps_wins'] += 1
        for m in overview:
            if m['match_id'] == r['match_id']:
                t1, t2 = [t.strip() for t in m['teams'].split(' vs ')]
                loser = t2 if winner == t1 else t1
            if loser in team_stats:
                team_stats[loser]['maps_losses'] += 1
            break
    
    
    for p in player_rows:
        team_abbr = p.get('team')
        team_full_name = None
        for full_name, abbr in TEAM_ABBREVIATIONS.items():
            if abbr == team_abbr:
                team_full_name = full_name
                break
        
        if team_full_name and team_full_name in team_stats:
            team_stats[team_full_name]['rating'] += parsear_float(p.get('rating'))
            team_stats[team_full_name]['acs'] += parsear_float(p.get('acs'))
            team_stats[team_full_name]['kast'] += parsear_porcentagem(p.get('kast'))
            team_stats[team_full_name]['player_count'] += 1
    
    for team in team_stats:
        if team_stats[team]['player_count'] > 0:
            team_stats[team]['rating'] /= team_stats[team]['player_count']
            team_stats[team]['acs'] /= team_stats[team]['player_count']
            team_stats[team]['kast'] /= team_stats[team]['player_count']
    
    headers = ["Posição", "Time", "Estágio de Eliminação", "Séries (W-L)", "Mapas (W-L)", "Rating médio", "ACS médio", "KAST médio"]
    rows = []
    
    for entry in official_ranking:
        team = entry['team']
        stats = team_stats.get(team, {})
        rows.append([
            entry['pos'],
            team,
            entry['stage'],
            f"{stats.get('series_wins', 0)}-{stats.get('series_losses', 0)}",
            f"{stats.get('maps_wins', 0)}-{stats.get('maps_losses', 0)}",
            f"{stats.get('rating', 0):.2f}",
            f"{stats.get('acs', 0):.1f}",
            f"{stats.get('kast', 0):.0f}%",
        ])
    
    fazer_tabela(headers, rows)


def listar_times_debug():
    headers = ["Nome Completo", "Abreviação"]
    rows = []
    for full_name, abbr in TEAM_ABBREVIATIONS.items():
        rows.append([full_name, abbr])
    
    print("=== TIMES DISPONÍVEIS ===")
    fazer_tabela(headers, rows)


def menu_debug():
    while True:
        print("\n=-= MENU DE DEBUG =-=")
        print("1 | Listar todos os times disponíveis")
        print("2 | Voltar ao menu principal")
        
        op = input("Escolha uma opção: ").strip()
        
        if op == '1':
            listar_times_debug()
        elif op == '2':
            break
        else:
            print("Opção inválida.")
        
        input("\nPressione Enter para continuar...")


def menu():
    print("-=-=-"*20)
    print("1 | Listar top 10 jogadores por performance geral")
    print("2 | Top 5 especialistas por agente")
    print("3 | Pickrate de agentes por mapa")
    print("4 | Comparar economia de times")
    print("5 | Intersecção de Players FK e Clutch%")
    print("6 | Analisar winrate em mapas picks e deciders de um time")
    print("7 | Ranking final de times com séries, mapas e média de performance.")
    print("8 | Menu de Debug")
    print("9 | Sair do programa")
    print("-=-=-"*20)


def principal():
    while True:
        menu()
        op = input("Escolha uma opção: ").strip().lower()
        if op == '1':
            listar_top10_performance()
        elif op == '2':
            top_5_especialistas()
        elif op == '3':
            pickrate_por_mapa()
        elif op == '4':
            comparar_economia_times()
        elif op == '5':
            jogadores_adaptativos()
        elif op == '6':
            analisar_winrate_pick()
        elif op == '7':
            ranking_final_times()
        elif op == '8':
            menu_debug()
        elif op == '9':
            break
        else:
            print("Opção inválida.")
        input("\nPressione Enter para continuar...\n")


if __name__ == '__main__':
    principal()