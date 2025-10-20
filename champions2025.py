import csv
import os
import re
import ast
from statistics import median, quantiles


# Utilidades de caminho e parsing
def resolve_path(file_name: str) -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    path_root = os.path.join(here, file_name)
    path_data = os.path.join(here, 'data', file_name)
    if os.path.exists(path_root):
        return path_root
    if os.path.exists(path_data):
        return path_data
    return path_root  


def read_csv_dicts(file_name: str):
    path = resolve_path(file_name)
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def parse_percent(value: str) -> float:
    if value is None:
        return 0.0
    s = str(value).strip().replace(',', '.')
    if s.endswith('%'):
        s = s[:-1]
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_float(value: str) -> float:
    if value is None:
        return 0.0
    s = str(value).strip().replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_int(value: str) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def parse_tuple_count_wins(text: str):
    if text is None:
        return 0, 0
    m = re.match(r"\s*(\d+)\s*\((\d+)\)\s*", str(text))
    if not m:
        n = parse_int(text)
        return n, 0
    total = int(m.group(1))
    wins = int(m.group(2))
    return total, wins


# Carregamento de dados principais
def load_player_stats():
    return read_csv_dicts('player_stats.csv')


def load_agents_stats():
    return read_csv_dicts('agents_stats.csv')


def load_maps_stats():
    return read_csv_dicts('maps_stats.csv')


def load_economy_data():
    return read_csv_dicts('economy_data.csv')


def load_performance_data():
    return read_csv_dicts('performance_data.csv')


# Impressão em tabela estilo MySQL
def print_table(headers, rows):
    if not headers or not rows:
        return
    
    headers = [str(h) for h in headers]
    rows = [[str(cell) for cell in row] for row in rows]
    
    # Calcular largura máxima de cada coluna
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(header)
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(row[i]))
        col_widths.append(max_width + 2)  # +2 para padding
    
    # Função para criar linha horizontal
    def make_line():
        return "+" + "+".join("-" * width for width in col_widths) + "+"
    
    # Função para criar linha de dados
    def make_row(cells):
        row_parts = []
        for i, cell in enumerate(cells):
            if i < len(col_widths):
                padded_cell = cell.ljust(col_widths[i] - 1)
                row_parts.append(padded_cell)
        return "|" + "|".join(row_parts) + "|"
    
    # Imprimir tabela
    print(make_line())
    print(make_row(headers))
    print(make_line())
    for row in rows:
        print(make_row(row))
    print(make_line())


# 1) Top 10 por performance geral
def listar_top10_performance():
    players = load_player_stats()
    for p in players:
        p['rating_num'] = parse_float(p.get('rating'))
        p['acs_num'] = parse_float(p.get('acs'))
        p['kast_num'] = parse_percent(p.get('kast'))
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
    print_table(headers, rows)


# 2) Top 5 especialistas por agente (aproximação usando KAST geral)
def top_5_especialistas_por_agente(agente_escolhido: str):
    players = load_player_stats()
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
            p['kast_num'] = parse_percent(p.get('kast'))
            p['rating_num'] = parse_float(p.get('rating'))
            p['acs_num'] = parse_float(p.get('acs'))
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
            f"{parse_percent(p.get('kast')):.0f}%",
            f"{parse_float(p.get('rating')):.2f}",
            f"{parse_float(p.get('acs')):.1f}",
        ])
    print_table(headers, rows)


# 3) Pickrate e (sem winrate) por agente em mapa
def pickrate_e_winrate_por_agente_em_mapa(mapa_escolhido: str):
    stats = load_agents_stats()
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
        pick = parse_float(row.get(mapa_norm))
        linhas.append((agent, pick))
    linhas.sort(key=lambda x: x[1], reverse=True)

    headers = [f"Agente ({mapa_norm})", "Pickrate"]
    rows = [[agent, f"{pick:.1f}%"] for agent, pick in linhas]
    print_table(headers, rows)
    print("Winrate por agente no mapa: N/D (não disponível nos dados fornecidos)")


# 4) Comparar eficiência econômica entre dois times
def comparar_eficiencia_economica_times(time_a: str, time_b: str):
    # Mapear nomes completos para abreviações usadas no economy_data.csv
    team_mapping = {
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
        'Guangzhou Huadu Bilibili Gaming(Bilibili Gaming)': 'BLG'
    }
    
    # Converter nomes para abreviações
    team_a_abbr = team_mapping.get(time_a, time_a)
    team_b_abbr = team_mapping.get(time_b, time_b)
    
    econ = load_economy_data()
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
            total['pistol_won'] += parse_int(r.get('Pistol Won'))
            t, w = parse_tuple_count_wins(r.get('Eco (won)'))
            total['eco_total'] += t; total['eco_wins'] += w
            t, w = parse_tuple_count_wins(r.get('Semi-eco (won)'))
            total['semi_eco_total'] += t; total['semi_eco_wins'] += w
            t, w = parse_tuple_count_wins(r.get('Semi-buy (won)'))
            total['semi_buy_total'] += t; total['semi_buy_wins'] += w
            t, w = parse_tuple_count_wins(r.get('Full buy(won)'))
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
    print_table(headers, rows)


# 5) Interseção de jogadores adaptativos (FK ∩ Clutch%)
def interseccao_jogadores_adaptativos():
    players = load_player_stats()
    fk_list = []  # first_kills
    cl_list = []  # clutch percent
    for p in players:
        fk_list.append(parse_int(p.get('first_kills')))
        cl_list.append(parse_percent(p.get('cl_percent')))

    if not players:
        print("Sem dados de jogadores.")
        return

    # Usar quartis superiores (Q3) para definir 'alto'
    try:
        q_fk = quantiles(fk_list, n=4)[2]  # Q3
        q_cl = quantiles(cl_list, n=4)[2]
    except Exception:
        q_fk = median(fk_list)
        q_cl = median(cl_list)

    altos_fk = {p.get('player_name') for p in players if parse_int(p.get('first_kills')) >= q_fk}
    altos_cl = {p.get('player_name') for p in players if parse_percent(p.get('cl_percent')) >= q_cl}
    intersec = [p for p in players if p.get('player_name') in altos_fk and p.get('player_name') in altos_cl]

    headers = ["Jogador", "Time", "First Kills", "Clutch%"]
    rows = []
    for p in intersec:
        rows.append([
            p.get('player_name','?'),
            p.get('team','?'),
            parse_int(p.get('first_kills')),
            f"{parse_percent(p.get('cl_percent')):.0f}%",
        ])
    print_table(headers, rows)


def load_detailed_matches_maps():
    return read_csv_dicts('detailed_matches_maps.csv')


# Ranking final dos times: posição oficial do Champions 2025
def ranking_final_times():
    # Ranking oficial do Champions 2025
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
    
    # Carregar dados para estatísticas
    overview = read_csv_dicts('detailed_matches_overview.csv')
    maps_rows = load_detailed_matches_maps()
    player_rows = load_player_stats()
    
    # Calcular estatísticas por time
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
    
    # Contar séries vencidas/perdidas
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
    
    # Contar mapas vencidos/perdidos
    for r in maps_rows:
        winner = r['winner']
        if winner in team_stats:
            team_stats[winner]['maps_wins'] += 1
        # Encontrar perdedor
        for m in overview:
            if m['match_id'] == r['match_id']:
                t1, t2 = [t.strip() for t in m['teams'].split(' vs ')]
                loser = t2 if winner == t1 else t1
            if loser in team_stats:
                team_stats[loser]['maps_losses'] += 1
            break
    
    # Mapear nomes completos para abreviações usadas no player_stats.csv
    team_name_mapping = {
        'NRG': 'NRG',
        'FNATIC': 'FNC',
        'DRX': 'DRX', 
        'Paper Rex': 'PRX',
        'MIBR': 'MIBR',
        'Team Heretics': 'TH',
        'G2 Esports': 'G2',
        'GIANTX': 'GX',
        'Team Liquid': 'TL',
        'Xi Lai Gaming': 'XLG',
        'T1': 'T1',
        'Rex Regum Qeon': 'RRQ',
        'Sentinels': 'SEN',
        'EDward Gaming': 'EDG',
        'Bilibili Gaming': 'BLG',
        'Dragon Ranger Gaming': 'DRG'
    }
    
    # Calcular performance média por time
    for p in player_rows:
        team_abbr = p.get('team')
        # Encontrar o nome completo correspondente
        team_full_name = None
        for full_name, abbr in team_name_mapping.items():
            if abbr == team_abbr:
                team_full_name = full_name
                break
        
        if team_full_name and team_full_name in team_stats:
            team_stats[team_full_name]['rating'] += parse_float(p.get('rating'))
            team_stats[team_full_name]['acs'] += parse_float(p.get('acs'))
            team_stats[team_full_name]['kast'] += parse_percent(p.get('kast'))
            team_stats[team_full_name]['player_count'] += 1
    
    # Calcular médias
    for team in team_stats:
        if team_stats[team]['player_count'] > 0:
            team_stats[team]['rating'] /= team_stats[team]['player_count']
            team_stats[team]['acs'] /= team_stats[team]['player_count']
            team_stats[team]['kast'] /= team_stats[team]['player_count']
    
    # Criar tabela
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
    
    print_table(headers, rows)

# 6) Win Rate por cenário de pick/ban para um time
def analisar_winrate_por_pick_strategy(time_escolhido: str):
    time = (time_escolhido or '').strip()
    if not time:
        print("Time não informado.")
        return
    
    # Primeiro, encontrar todos os match_ids onde o time jogou
    overview = read_csv_dicts('detailed_matches_overview.csv')
    team_matches = {}
    for match in overview:
        if time in match['teams']:
            # Extrair adversário
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
    
    # Agora analisar apenas os mapas desses matches
    rows = load_detailed_matches_maps()
    contagem = {
        'proprio_pick': {'wins': 0, 'total': 0, 'details': []},
        'pick_adversario': {'wins': 0, 'total': 0, 'details': []},
        'decider': {'wins': 0, 'total': 0, 'details': []},
    }

    for r in rows:
        match_id = r.get('match_id')
        # Só analisar mapas de partidas onde o time jogou
        if match_id not in team_matches:
            continue
            
        picked_by = str(r.get('picked_by','')).strip()
        winner = str(r.get('winner','')).strip()
        map_name = r.get('map_name', '')
        score = r.get('score', '')
        
        # determinar categoria
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
        
        # Adicionar detalhes
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

    # Resumo geral
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
    print_table(headers, rows)
    
    # Detalhes por categoria
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
            print_table(details_headers, details_rows)


# Funções de Debug
def debug_listar_times():
    """Lista todos os times disponíveis com suas abreviações"""
    team_mapping = {
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
        'Guangzhou Huadu Bilibili Gaming(Bilibili Gaming)': 'BLG'
    }
    
    headers = ["Nome Completo", "Abreviação"]
    rows = []
    for full_name, abbr in team_mapping.items():
        rows.append([full_name, abbr])
    
    print("=== TIMES DISPONÍVEIS ===")
    print_table(headers, rows)


def debug_menu():
    """Menu de debug com opções de diagnóstico"""
    while True:
        print("\n=== MENU DE DEBUG ===")
        print("1. Listar todos os times disponíveis")
        print("2. Voltar ao menu principal")
        
        op = input("Escolha uma opção: ").strip()
        
        if op == '1':
            debug_listar_times()
        elif op == '2':
            break
        else:
            print("Opção inválida.")
        
        input("\nPressione Enter para continuar...")


def menu():
    print("1. Listar top 10 jogadores por performance geral") #Requisito: Ordenar (KAST, Rating, ACS).
    print("2. Top 5 especialistas por agente") #Requisito: Agrupar (Top por Agente e KAST).
    print("3. Pickrate e winrate por agente em mapa") #Requisito: Pesquisar por 2 atributos (Agente e Mapa).
    print("4. Comparar economia de times") #Requisito: Comparar/Média (Economia).
    print("5. Intersecção de Players que mais agregam valor em rounds") #Requisito: Conjuntos (Intersecção de First Kills e Clutches).
    print("6. Analisar winrate em mapas picks e deciders de um time") #Requisito: Profundidade do Map Pool.
    print("7. Ranking final de times com séries, mapas e média de performance.") #Ranking final de times com séries, mapas e média de performance.
    print("8. Menu de Debug") #Menu de debug com funções auxiliares.
    print("9. Sair do programa")


def main():
    while True:
        menu()
        op = input("Escolha uma opção: ").strip().lower()
        if op == '1':
            listar_top10_performance()
        elif op == '2':
            agente = input("Agente: ").strip()
            top_5_especialistas_por_agente(agente)
        elif op == '3':
            mapa = input("Mapa: ").strip()
            pickrate_e_winrate_por_agente_em_mapa(mapa)
        elif op == '4':
            a = input("Time A: ").strip()
            b = input("Time B: ").strip()
            comparar_eficiencia_economica_times(a, b)
        elif op == '5':
            interseccao_jogadores_adaptativos()
        elif op == '6':
            t = input("Time: ").strip()
            analisar_winrate_por_pick_strategy(t)
        elif op == '7':
            ranking_final_times()
        elif op == '8':
            debug_menu()
        elif op == '9':
            break
        else:
            print("Opção inválida.")
        input("\nPressione Enter para continuar...\n")


if __name__ == '__main__':
    main()