#!/usr/bin/env python3
"""
NFL PickEm 2025/2026 - Simplified Version
Name-only login system for maximum reliability
"""

from flask import Flask, request, jsonify, render_template, session
import sqlite3
import requests
from datetime import datetime, timedelta
import pytz
import os

app = Flask(__name__)
app.secret_key = 'nfl_pickem_2025_simple_login'

# Database path
DB_PATH = 'nfl_pickem.db'

# Vienna timezone
VIENNA_TZ = pytz.timezone('Europe/Vienna')

# Valid users (no passwords needed)
VALID_USERS = {
    1: 'Manuel',
    2: 'Daniel', 
    3: 'Raff',
    4: 'Haunschi'
}

# Team mapping for ESPN API
TEAM_MAPPING = {
    'ARI': 1, 'ATL': 2, 'BAL': 3, 'BUF': 4, 'CAR': 5, 'CHI': 6,
    'CIN': 7, 'CLE': 8, 'DAL': 9, 'DEN': 10, 'DET': 11, 'GB': 12,
    'HOU': 13, 'IND': 14, 'JAX': 15, 'KC': 16, 'LV': 17, 'LAC': 18,
    'LAR': 19, 'MIA': 20, 'MIN': 21, 'NE': 22, 'NO': 23, 'NYG': 24,
    'NYJ': 25, 'PHI': 26, 'PIT': 27, 'SF': 28, 'SEA': 29, 'TB': 30,
    'TEN': 31, 'WAS': 32
}

def init_database():
    """Initialize database with guaranteed user creation"""
    print("🏈 Initializing NFL PickEm database...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            abbreviation TEXT NOT NULL,
            logo_url TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            week INTEGER NOT NULL,
            home_team_id INTEGER NOT NULL,
            away_team_id INTEGER NOT NULL,
            game_time TEXT NOT NULL,
            is_completed BOOLEAN DEFAULT FALSE,
            home_score INTEGER,
            away_score INTEGER,
            FOREIGN KEY (home_team_id) REFERENCES teams (id),
            FOREIGN KEY (away_team_id) REFERENCES teams (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS picks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            week INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            is_correct BOOLEAN,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (match_id) REFERENCES matches (id),
            FOREIGN KEY (team_id) REFERENCES teams (id),
            UNIQUE(user_id, week)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_picks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            week INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            is_correct BOOLEAN NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (team_id) REFERENCES teams (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            usage_type TEXT NOT NULL CHECK (usage_type IN ('winner', 'loser')),
            week INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (team_id) REFERENCES teams (id)
        )
    """)
    
    # Create users (simplified - no passwords)
    for user_id, username in VALID_USERS.items():
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, username)
            VALUES (?, ?)
        """, (user_id, username))
    
    print("✅ Users created: Manuel, Daniel, Raff, Haunschi")
    
    # Create teams
    teams = [
        (1, 'Arizona Cardinals', 'ARI', 'https://a.espncdn.com/i/teamlogos/nfl/500/ari.png'),
        (2, 'Atlanta Falcons', 'ATL', 'https://a.espncdn.com/i/teamlogos/nfl/500/atl.png'),
        (3, 'Baltimore Ravens', 'BAL', 'https://a.espncdn.com/i/teamlogos/nfl/500/bal.png'),
        (4, 'Buffalo Bills', 'BUF', 'https://a.espncdn.com/i/teamlogos/nfl/500/buf.png'),
        (5, 'Carolina Panthers', 'CAR', 'https://a.espncdn.com/i/teamlogos/nfl/500/car.png'),
        (6, 'Chicago Bears', 'CHI', 'https://a.espncdn.com/i/teamlogos/nfl/500/chi.png'),
        (7, 'Cincinnati Bengals', 'CIN', 'https://a.espncdn.com/i/teamlogos/nfl/500/cin.png'),
        (8, 'Cleveland Browns', 'CLE', 'https://a.espncdn.com/i/teamlogos/nfl/500/cle.png'),
        (9, 'Dallas Cowboys', 'DAL', 'https://a.espncdn.com/i/teamlogos/nfl/500/dal.png'),
        (10, 'Denver Broncos', 'DEN', 'https://a.espncdn.com/i/teamlogos/nfl/500/den.png'),
        (11, 'Detroit Lions', 'DET', 'https://a.espncdn.com/i/teamlogos/nfl/500/det.png'),
        (12, 'Green Bay Packers', 'GB', 'https://a.espncdn.com/i/teamlogos/nfl/500/gb.png'),
        (13, 'Houston Texans', 'HOU', 'https://a.espncdn.com/i/teamlogos/nfl/500/hou.png'),
        (14, 'Indianapolis Colts', 'IND', 'https://a.espncdn.com/i/teamlogos/nfl/500/ind.png'),
        (15, 'Jacksonville Jaguars', 'JAX', 'https://a.espncdn.com/i/teamlogos/nfl/500/jax.png'),
        (16, 'Kansas City Chiefs', 'KC', 'https://a.espncdn.com/i/teamlogos/nfl/500/kc.png'),
        (17, 'Las Vegas Raiders', 'LV', 'https://a.espncdn.com/i/teamlogos/nfl/500/lv.png'),
        (18, 'Los Angeles Chargers', 'LAC', 'https://a.espncdn.com/i/teamlogos/nfl/500/lac.png'),
        (19, 'Los Angeles Rams', 'LAR', 'https://a.espncdn.com/i/teamlogos/nfl/500/lar.png'),
        (20, 'Miami Dolphins', 'MIA', 'https://a.espncdn.com/i/teamlogos/nfl/500/mia.png'),
        (21, 'Minnesota Vikings', 'MIN', 'https://a.espncdn.com/i/teamlogos/nfl/500/min.png'),
        (22, 'New England Patriots', 'NE', 'https://a.espncdn.com/i/teamlogos/nfl/500/ne.png'),
        (23, 'New Orleans Saints', 'NO', 'https://a.espncdn.com/i/teamlogos/nfl/500/no.png'),
        (24, 'New York Giants', 'NYG', 'https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png'),
        (25, 'New York Jets', 'NYJ', 'https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png'),
        (26, 'Philadelphia Eagles', 'PHI', 'https://a.espncdn.com/i/teamlogos/nfl/500/phi.png'),
        (27, 'Pittsburgh Steelers', 'PIT', 'https://a.espncdn.com/i/teamlogos/nfl/500/pit.png'),
        (28, 'San Francisco 49ers', 'SF', 'https://a.espncdn.com/i/teamlogos/nfl/500/sf.png'),
        (29, 'Seattle Seahawks', 'SEA', 'https://a.espncdn.com/i/teamlogos/nfl/500/sea.png'),
        (30, 'Tampa Bay Buccaneers', 'TB', 'https://a.espncdn.com/i/teamlogos/nfl/500/tb.png'),
        (31, 'Tennessee Titans', 'TEN', 'https://a.espncdn.com/i/teamlogos/nfl/500/ten.png'),
        (32, 'Washington Commanders', 'WAS', 'https://a.espncdn.com/i/teamlogos/nfl/500/was.png')
    ]
    
    for team_id, name, abbr, logo in teams:
        cursor.execute("""
            INSERT OR REPLACE INTO teams (id, name, abbreviation, logo_url)
            VALUES (?, ?, ?, ?)
        """, (team_id, name, abbr, logo))
    
    print("✅ 32 NFL teams created")
    
    # Add historical picks for W1+W2 (correct data)
    historical_picks = [
        # Week 1
        (1, 1, 2, False, '2025-09-05 20:00:00'),  # Manuel: Falcons (lost)
        (2, 1, 10, True, '2025-09-05 20:00:00'),  # Daniel: Broncos (won)
        (3, 1, 7, True, '2025-09-05 20:00:00'),   # Raff: Bengals (won)
        (4, 1, 32, True, '2025-09-05 20:00:00'),  # Haunschi: Commanders (won)
        
        # Week 2
        (1, 2, 9, True, '2025-09-12 20:00:00'),   # Manuel: Cowboys (won)
        (2, 2, 26, True, '2025-09-12 20:00:00'),  # Daniel: Eagles (won)
        (3, 2, 9, True, '2025-09-12 20:00:00'),   # Raff: Cowboys (won)
        (4, 2, 4, True, '2025-09-12 20:00:00'),   # Haunschi: Bills (won)
    ]
    
    for user_id, week, team_id, is_correct, created_at in historical_picks:
        cursor.execute("""
            INSERT OR REPLACE INTO historical_picks (user_id, week, team_id, is_correct, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, week, team_id, is_correct, created_at))
    
    print("✅ Historical picks W1+W2 created")
    
    # Add correct team usage based on historical picks
    team_usage_data = [
        # Manuel W1: Falcons winner -> Buccaneers loser
        (1, 2, 'winner', 1),   # Manuel: Falcons winner
        (1, 30, 'loser', 1),   # Manuel: Buccaneers loser
        
        # Manuel W2: Cowboys winner -> Giants loser  
        (1, 9, 'winner', 2),   # Manuel: Cowboys winner
        (1, 24, 'loser', 2),   # Manuel: Giants loser
        
        # Daniel W1: Broncos winner -> Titans loser
        (2, 10, 'winner', 1),  # Daniel: Broncos winner
        (2, 31, 'loser', 1),   # Daniel: Titans loser
        
        # Daniel W2: Eagles winner -> Chiefs loser
        (2, 26, 'winner', 2),  # Daniel: Eagles winner
        (2, 16, 'loser', 2),   # Daniel: Chiefs loser
        
        # Raff W1: Bengals winner -> Browns loser
        (3, 7, 'winner', 1),   # Raff: Bengals winner
        (3, 8, 'loser', 1),    # Raff: Browns loser
        
        # Raff W2: Cowboys winner -> Giants loser
        (3, 9, 'winner', 2),   # Raff: Cowboys winner
        (3, 24, 'loser', 2),   # Raff: Giants loser
        
        # Haunschi W1: Commanders winner -> Giants loser
        (4, 32, 'winner', 1),  # Haunschi: Commanders winner
        (4, 24, 'loser', 1),   # Haunschi: Giants loser
        
        # Haunschi W2: Bills winner -> Dolphins loser
        (4, 4, 'winner', 2),   # Haunschi: Bills winner
        (4, 20, 'loser', 2),   # Haunschi: Dolphins loser
    ]
    
    for user_id, team_id, usage_type, week in team_usage_data:
        cursor.execute("""
            INSERT OR REPLACE INTO team_usage (user_id, team_id, usage_type, week)
            VALUES (?, ?, ?, ?)
        """, (user_id, team_id, usage_type, week))
    
    print("✅ Team usage created (correct W1+W2 data)")
    
    # Add sample NFL games for Week 3 (will be replaced by ESPN data)
    sample_games = [
        (1, 3, 20, 4, '2025-09-21 22:25:00'),    # Miami @ Buffalo
        (2, 3, 12, 8, '2025-09-22 19:00:00'),    # Green Bay @ Cleveland
        (3, 3, 14, 31, '2025-09-22 19:00:00'),   # Indianapolis @ Tennessee
        (4, 3, 7, 21, '2025-09-22 19:00:00'),    # Cincinnati @ Minnesota
        (5, 3, 27, 22, '2025-09-22 19:00:00'),   # Pittsburgh @ New England
        (6, 3, 1, 28, '2025-09-22 22:05:00'),    # Arizona @ San Francisco
        (7, 3, 2, 5, '2025-09-22 22:25:00'),     # Atlanta @ Carolina
        (8, 3, 9, 6, '2025-09-22 22:25:00'),     # Dallas @ Chicago
        (9, 3, 11, 3, '2025-09-23 02:20:00'),    # Detroit @ Baltimore
        (10, 3, 13, 15, '2025-09-23 02:20:00'),  # Houston @ Jacksonville
        (11, 3, 16, 24, '2025-09-23 02:20:00'),  # Kansas City @ Giants
        (12, 3, 18, 10, '2025-09-23 02:20:00'),  # Chargers @ Denver
        (13, 3, 19, 29, '2025-09-23 02:20:00'),  # Rams @ Seattle
        (14, 3, 23, 26, '2025-09-23 02:20:00'),  # Saints @ Eagles
        (15, 3, 25, 30, '2025-09-23 02:20:00'),  # Jets @ Buccaneers
        (16, 3, 17, 32, '2025-09-23 02:20:00'),  # Raiders @ Commanders
    ]
    
    for game_id, week, away_id, home_id, game_time in sample_games:
        cursor.execute("""
            INSERT OR REPLACE INTO matches (id, week, home_team_id, away_team_id, game_time, is_completed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (game_id, week, home_id, away_id, game_time, False))
    
    print("✅ 16 sample NFL games for Week 3 created")
    
    conn.commit()
    conn.close()
    
    print("🎉 Database initialization complete!")

# Initialize database on startup
if not os.path.exists(DB_PATH):
    init_database()

@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('index.html', logged_in=False, valid_users=list(VALID_USERS.values()))
    return render_template('index.html', logged_in=True, username=session['username'])

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'success': False, 'message': 'Benutzername erforderlich'}), 400
        
        # Find user by name
        user_id = None
        for uid, uname in VALID_USERS.items():
            if uname == username:
                user_id = uid
                break
        
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            return jsonify({'success': True, 'message': f'Willkommen {username}!'})
        else:
            return jsonify({'success': False, 'message': 'Ungültiger Benutzername'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server-Fehler: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logout erfolgreich'})

@app.route('/api/dashboard')
def dashboard():
    if 'user_id' not in session:
        return jsonify({'error': 'Nicht angemeldet'}), 401
    
    try:
        user_id = session['user_id']
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Current week (always 3 for now)
        current_week = 3
        
        # Total points from historical picks
        cursor.execute("""
            SELECT COUNT(*) FROM historical_picks 
            WHERE user_id = ? AND is_correct = 1
        """, (user_id,))
        total_points = cursor.fetchone()[0]
        
        # Correct picks from historical data
        cursor.execute("""
            SELECT COUNT(*) FROM historical_picks 
            WHERE user_id = ? AND is_correct = 1
        """, (user_id,))
        correct_picks = cursor.fetchone()[0]
        
        # Total historical picks
        cursor.execute("""
            SELECT COUNT(*) FROM historical_picks 
            WHERE user_id = ?
        """, (user_id,))
        total_historical = cursor.fetchone()[0]
        
        # Team usage
        cursor.execute("""
            SELECT t.name, tu.usage_type
            FROM team_usage tu
            JOIN teams t ON tu.team_id = t.id
            WHERE tu.user_id = ?
            ORDER BY tu.usage_type, t.name
        """, (user_id,))
        
        team_usage_raw = cursor.fetchall()
        winner_teams = [name for name, usage_type in team_usage_raw if usage_type == 'winner']
        loser_teams = [name for name, usage_type in team_usage_raw if usage_type == 'loser']
        
        # Current rank
        cursor.execute("""
            SELECT user_id, 
                   (SELECT COUNT(*) FROM historical_picks hp2 WHERE hp2.user_id = hp.user_id AND hp2.is_correct = 1) as points
            FROM historical_picks hp
            GROUP BY user_id
            ORDER BY points DESC
        """)
        
        rankings = cursor.fetchall()
        current_rank = 1
        for i, (uid, points) in enumerate(rankings):
            if uid == user_id:
                current_rank = i + 1
                break
        
        conn.close()
        
        return jsonify({
            'current_week': current_week,
            'total_points': total_points,
            'correct_picks': correct_picks,
            'total_picks': total_historical,
            'current_rank': current_rank,
            'winner_teams': winner_teams,
            'loser_teams': loser_teams
        })
        
    except Exception as e:
        return jsonify({'error': f'Dashboard-Fehler: {str(e)}'}), 500

@app.route('/api/matches/<int:week>')
def get_matches(week):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.id, m.week, m.game_time, m.is_completed,
                   ht.name as home_team, ht.logo_url as home_logo,
                   at.name as away_team, at.logo_url as away_logo,
                   ht.id as home_team_id, at.id as away_team_id,
                   m.home_score, m.away_score
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE m.week = ?
            ORDER BY m.game_time
        """, (week,))
        
        matches = []
        for row in cursor.fetchall():
            match_id, week, game_time, is_completed, home_team, home_logo, away_team, away_logo, home_team_id, away_team_id, home_score, away_score = row
            
            # Parse game time
            try:
                game_dt = datetime.fromisoformat(game_time)
                if game_dt.tzinfo is None:
                    game_dt = VIENNA_TZ.localize(game_dt)
                formatted_time = game_dt.strftime('%a., %d.%m, %H:%M')
            except:
                formatted_time = game_time
            
            match_data = {
                'id': match_id,
                'week': week,
                'home_team': home_team,
                'away_team': away_team,
                'home_logo': home_logo,
                'away_logo': away_logo,
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'game_time': formatted_time,
                'is_completed': bool(is_completed)
            }
            
            if is_completed and home_score is not None and away_score is not None:
                match_data['home_score'] = home_score
                match_data['away_score'] = away_score
            
            matches.append(match_data)
        
        conn.close()
        return jsonify(matches)
        
    except Exception as e:
        return jsonify({'error': f'Fehler beim Laden der Spiele: {str(e)}'}), 500

@app.route('/api/picks', methods=['POST'])
def submit_pick():
    if 'user_id' not in session:
        return jsonify({'error': 'Nicht angemeldet'}), 401
    
    try:
        data = request.get_json()
        match_id = data.get('match_id')
        team_id = data.get('team_id')
        week = data.get('week')
        
        if not all([match_id, team_id, week]):
            return jsonify({'error': 'Unvollständige Daten'}), 400
        
        user_id = session['user_id']
        
        # Team usage validation
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check winner usage (max 2x)
        cursor.execute("""
            SELECT COUNT(*) FROM team_usage 
            WHERE user_id = ? AND team_id = ? AND usage_type = 'winner'
        """, (user_id, team_id))
        winner_count = cursor.fetchone()[0]
        
        if winner_count >= 2:
            team_name = cursor.execute("SELECT name FROM teams WHERE id = ?", (team_id,)).fetchone()[0]
            return jsonify({'error': f'{team_name} wurde bereits 2x als Gewinner gewählt'}), 400
        
        # Get opponent team for loser validation
        cursor.execute("""
            SELECT home_team_id, away_team_id FROM matches WHERE id = ?
        """, (match_id,))
        match_info = cursor.fetchone()
        if not match_info:
            return jsonify({'error': 'Spiel nicht gefunden'}), 400
        
        home_team_id, away_team_id = match_info
        opponent_team_id = away_team_id if team_id == home_team_id else home_team_id
        
        # Check if opponent is already eliminated as loser
        cursor.execute("""
            SELECT COUNT(*) FROM team_usage 
            WHERE user_id = ? AND team_id = ? AND usage_type = 'loser'
        """, (user_id, opponent_team_id))
        loser_count = cursor.fetchone()[0]
        
        if loser_count >= 1:
            opponent_name = cursor.execute("SELECT name FROM teams WHERE id = ?", (opponent_team_id,)).fetchone()[0]
            return jsonify({'error': f'{opponent_name} wurde bereits als Verlierer gewählt'}), 400
        
        # Save pick
        created_at = datetime.now(VIENNA_TZ).isoformat()
        
        cursor.execute("""
            INSERT OR REPLACE INTO picks (user_id, match_id, team_id, week, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, match_id, team_id, week, created_at))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Pick gespeichert'})
        
    except Exception as e:
        return jsonify({'error': f'Fehler beim Speichern: {str(e)}'}), 500

@app.route('/api/leaderboard')
def leaderboard():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all users with their points from historical picks
        cursor.execute("""
            SELECT u.id, u.username,
                   COALESCE(SUM(CASE WHEN hp.is_correct = 1 THEN 1 ELSE 0 END), 0) as points,
                   COUNT(hp.id) as total_picks,
                   COALESCE(SUM(CASE WHEN hp.is_correct = 1 THEN 1 ELSE 0 END), 0) as correct_picks
            FROM users u
            LEFT JOIN historical_picks hp ON u.id = hp.user_id
            GROUP BY u.id, u.username
            ORDER BY points DESC, total_picks DESC
        """)
        
        users_data = cursor.fetchall()
        
        # Calculate ranks (same points = same rank)
        leaderboard_data = []
        current_rank = 1
        prev_points = None
        
        for i, (user_id, username, points, total_picks, correct_picks) in enumerate(users_data):
            if prev_points is not None and points != prev_points:
                current_rank = i + 1
            
            leaderboard_data.append({
                'rank': current_rank,
                'username': username,
                'points': points,
                'total_picks': total_picks,
                'correct_picks': correct_picks
            })
            
            prev_points = points
        
        conn.close()
        return jsonify(leaderboard_data)
        
    except Exception as e:
        return jsonify({'error': f'Leaderboard-Fehler: {str(e)}'}), 500

@app.route('/api/all-picks')
def all_picks():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all historical picks with team names
        cursor.execute("""
            SELECT hp.week, u.username, t.name as team_name, hp.is_correct, hp.created_at
            FROM historical_picks hp
            JOIN users u ON hp.user_id = u.id
            JOIN teams t ON hp.team_id = t.id
            ORDER BY hp.week DESC, u.username
        """)
        
        picks_data = cursor.fetchall()
        
        # Group by week
        picks_by_week = {}
        for week, username, team_name, is_correct, created_at in picks_data:
            if week not in picks_by_week:
                picks_by_week[week] = []
            
            # Format date
            try:
                pick_date = datetime.fromisoformat(created_at)
                formatted_date = pick_date.strftime('%d.%m.%Y')
            except:
                formatted_date = created_at
            
            picks_by_week[week].append({
                'username': username,
                'team_name': team_name,
                'is_correct': bool(is_correct),
                'date': formatted_date
            })
        
        conn.close()
        return jsonify(picks_by_week)
        
    except Exception as e:
        return jsonify({'error': f'Fehler beim Laden der Picks: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
