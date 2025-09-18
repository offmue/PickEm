#!/usr/bin/env python3
"""
NFL PickEm 2025/2026 - Dashboard Critical Fix
✅ Fixed API endpoints returning proper JSON data
✅ Simple login (name dropdown)
✅ All weeks W1-W18 available  
✅ Vienna timezone conversion
✅ Pick saving functionality
✅ Team graying implementation
"""

from flask import Flask, request, jsonify, render_template, session
import sqlite3
import requests
from datetime import datetime, timedelta
import pytz
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'nfl_pickem_2025_dashboard_fixed')

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

# NFL Teams with ESPN IDs
NFL_TEAMS = {
    1: {'name': 'Arizona Cardinals', 'abbr': 'ARI', 'espn_id': 22},
    2: {'name': 'Atlanta Falcons', 'abbr': 'ATL', 'espn_id': 1},
    3: {'name': 'Baltimore Ravens', 'abbr': 'BAL', 'espn_id': 33},
    4: {'name': 'Buffalo Bills', 'abbr': 'BUF', 'espn_id': 2},
    5: {'name': 'Carolina Panthers', 'abbr': 'CAR', 'espn_id': 29},
    6: {'name': 'Chicago Bears', 'abbr': 'CHI', 'espn_id': 3},
    7: {'name': 'Cincinnati Bengals', 'abbr': 'CIN', 'espn_id': 4},
    8: {'name': 'Cleveland Browns', 'abbr': 'CLE', 'espn_id': 5},
    9: {'name': 'Dallas Cowboys', 'abbr': 'DAL', 'espn_id': 6},
    10: {'name': 'Denver Broncos', 'abbr': 'DEN', 'espn_id': 7},
    11: {'name': 'Detroit Lions', 'abbr': 'DET', 'espn_id': 8},
    12: {'name': 'Green Bay Packers', 'abbr': 'GB', 'espn_id': 9},
    13: {'name': 'Houston Texans', 'abbr': 'HOU', 'espn_id': 34},
    14: {'name': 'Indianapolis Colts', 'abbr': 'IND', 'espn_id': 11},
    15: {'name': 'Jacksonville Jaguars', 'abbr': 'JAX', 'espn_id': 30},
    16: {'name': 'Kansas City Chiefs', 'abbr': 'KC', 'espn_id': 12},
    17: {'name': 'Las Vegas Raiders', 'abbr': 'LV', 'espn_id': 13},
    18: {'name': 'Los Angeles Chargers', 'abbr': 'LAC', 'espn_id': 24},
    19: {'name': 'Los Angeles Rams', 'abbr': 'LAR', 'espn_id': 14},
    20: {'name': 'Miami Dolphins', 'abbr': 'MIA', 'espn_id': 15},
    21: {'name': 'Minnesota Vikings', 'abbr': 'MIN', 'espn_id': 16},
    22: {'name': 'New England Patriots', 'abbr': 'NE', 'espn_id': 17},
    23: {'name': 'New Orleans Saints', 'abbr': 'NO', 'espn_id': 18},
    24: {'name': 'New York Giants', 'abbr': 'NYG', 'espn_id': 19},
    25: {'name': 'New York Jets', 'abbr': 'NYJ', 'espn_id': 20},
    26: {'name': 'Philadelphia Eagles', 'abbr': 'PHI', 'espn_id': 21},
    27: {'name': 'Pittsburgh Steelers', 'abbr': 'PIT', 'espn_id': 23},
    28: {'name': 'San Francisco 49ers', 'abbr': 'SF', 'espn_id': 25},
    29: {'name': 'Seattle Seahawks', 'abbr': 'SEA', 'espn_id': 26},
    30: {'name': 'Tampa Bay Buccaneers', 'abbr': 'TB', 'espn_id': 27},
    31: {'name': 'Tennessee Titans', 'abbr': 'TEN', 'espn_id': 10},
    32: {'name': 'Washington Commanders', 'abbr': 'WAS', 'espn_id': 28}
}

def init_database():
    """Initialize database with all necessary tables and REAL historical data"""
    print("🏈 Initializing NFL PickEm database with REAL data...")
    
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
            logo_url TEXT,
            espn_id INTEGER
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
            team_name TEXT NOT NULL,
            team_id INTEGER,
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
            usage_type TEXT NOT NULL,
            week INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (team_id) REFERENCES teams (id)
        )
    """)
    
    # Insert users
    for user_id, username in VALID_USERS.items():
        cursor.execute("INSERT OR REPLACE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    
    # Insert teams
    for team_id, team_data in NFL_TEAMS.items():
        cursor.execute("""
            INSERT OR REPLACE INTO teams (id, name, abbreviation, logo_url, espn_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (
            team_id, 
            team_data['name'], 
            team_data['abbr'],
            f"https://a.espncdn.com/i/teamlogos/nfl/500/{team_data['abbr'].lower()}.png",
            team_data['espn_id']
        ))
    
    # Insert REAL historical picks (W1+W2) - GUARANTEED DATA
    historical_data = [
        # Manuel: W1 Falcons (loser), W2 Cowboys (winner) = 1 point
        (1, 1, 'Atlanta Falcons', 2, False, '2025-09-08T19:00:00'),
        (1, 2, 'Dallas Cowboys', 9, True, '2025-09-15T19:00:00'),
        
        # Daniel: W1 Broncos (winner), W2 Eagles (winner) = 2 points  
        (2, 1, 'Denver Broncos', 10, True, '2025-09-08T19:00:00'),
        (2, 2, 'Philadelphia Eagles', 26, True, '2025-09-15T19:00:00'),
        
        # Raff: W1 Bengals (winner), W2 Cowboys (winner) = 2 points
        (3, 1, 'Cincinnati Bengals', 7, True, '2025-09-08T19:00:00'),
        (3, 2, 'Dallas Cowboys', 9, True, '2025-09-15T19:00:00'),
        
        # Haunschi: W1 Commanders (winner), W2 Bills (winner) = 2 points
        (4, 1, 'Washington Commanders', 32, True, '2025-09-08T19:00:00'),
        (4, 2, 'Buffalo Bills', 4, True, '2025-09-15T19:00:00')
    ]
    
    for user_id, week, team_name, team_id, is_correct, created_at in historical_data:
        cursor.execute("""
            INSERT OR REPLACE INTO historical_picks (user_id, week, team_name, team_id, is_correct, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, week, team_name, team_id, is_correct, created_at))
    
    # Insert REAL team usage (W1+W2)
    team_usage_data = [
        # Manuel: Falcons loser W1, Cowboys winner W2
        (1, 2, 'loser', 1, '2025-09-08T19:00:00'),   
        (1, 9, 'winner', 2, '2025-09-15T19:00:00'),  
        
        # Daniel: Broncos winner W1, Eagles winner W2
        (2, 10, 'winner', 1, '2025-09-08T19:00:00'), 
        (2, 26, 'winner', 2, '2025-09-15T19:00:00'), 
        
        # Raff: Bengals winner W1, Cowboys winner W2
        (3, 7, 'winner', 1, '2025-09-08T19:00:00'),  
        (3, 9, 'winner', 2, '2025-09-15T19:00:00'),  
        
        # Haunschi: Commanders winner W1, Bills winner W2
        (4, 32, 'winner', 1, '2025-09-08T19:00:00'), 
        (4, 4, 'winner', 2, '2025-09-15T19:00:00')   
    ]
    
    for user_id, team_id, usage_type, week, created_at in team_usage_data:
        cursor.execute("""
            INSERT OR REPLACE INTO team_usage (user_id, team_id, usage_type, week, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, team_id, usage_type, week, created_at))
    
    # Create sample games for all weeks W1-W18
    create_sample_games_all_weeks(cursor)
    
    conn.commit()
    conn.close()
    print("✅ Database initialization complete with REAL data!")

def create_sample_games_all_weeks(cursor):
    """Create sample games for all 18 weeks"""
    print("🏈 Creating sample games for all 18 weeks...")
    
    # Sample matchups for each week (simplified)
    sample_matchups = [
        (1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 16),
        (17, 18), (19, 20), (21, 22), (23, 24), (25, 26), (27, 28), (29, 30), (31, 32)
    ]
    
    for week in range(1, 19):  # W1-W18
        game_id_start = (week - 1) * 16 + 1
        
        for i, (away_id, home_id) in enumerate(sample_matchups):
            game_id = game_id_start + i
            
            # Calculate game time (Vienna timezone)
            base_date = datetime(2025, 9, 7) + timedelta(weeks=week-1)  # Start from Week 1
            game_time = base_date + timedelta(days=i % 3, hours=19 + (i % 3))  # Spread across 3 days
            vienna_time = VIENNA_TZ.localize(game_time)
            
            cursor.execute("""
                INSERT OR REPLACE INTO matches (id, week, home_team_id, away_team_id, game_time, is_completed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (game_id, week, home_id, away_id, vienna_time.isoformat(), week <= 2))
    
    print("✅ Sample games created for all 18 weeks")

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
            return jsonify({'success': True, 'message': f'Willkommen, {username}!'})
        else:
            return jsonify({'success': False, 'message': 'Ungültiger Benutzername'}), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Server-Fehler beim Login'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Erfolgreich abgemeldet'})

@app.route('/api/dashboard')
def dashboard():
    """Get dashboard data - FIXED to return proper format"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Nicht angemeldet'}), 401
        
        user_id = session['user_id']
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get historical picks for points calculation
        cursor.execute("SELECT is_correct FROM historical_picks WHERE user_id = ?", (user_id,))
        historical_picks = cursor.fetchall()
        total_points = sum(1 for pick in historical_picks if pick[0])
        correct_picks = total_points
        total_picks = len(historical_picks)
        
        # Get team usage with team names
        cursor.execute("""
            SELECT t.name, tu.usage_type 
            FROM team_usage tu 
            JOIN teams t ON tu.team_id = t.id 
            WHERE tu.user_id = ?
        """, (user_id,))
        team_usage = cursor.fetchall()
        
        winner_teams = [row[0] for row in team_usage if row[1] == 'winner']
        loser_teams = [row[0] for row in team_usage if row[1] == 'loser']
        
        # Calculate rank - FIXED to handle all users properly
        cursor.execute("""
            SELECT u.id, u.username, COUNT(CASE WHEN hp.is_correct = 1 THEN 1 END) as points
            FROM users u
            LEFT JOIN historical_picks hp ON u.id = hp.user_id
            GROUP BY u.id, u.username
            ORDER BY points DESC
        """)
        rankings = cursor.fetchall()
        
        rank = 1
        for i, (uid, uname, points) in enumerate(rankings):
            if uid == user_id:
                rank = i + 1
                break
        
        conn.close()
        
        # Return GUARANTEED proper format
        return jsonify({
            'success': True,
            'data': {
                'current_week': 3,
                'picks_submitted': 1 if total_picks > 0 else 0,
                'total_points': total_points,
                'correct_picks': correct_picks,
                'total_picks': total_picks,
                'rank': rank,
                'winner_teams': winner_teams,
                'loser_teams': loser_teams
            }
        })
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return jsonify({'success': False, 'message': 'Fehler beim Laden des Dashboards'}), 500

@app.route('/api/leaderboard')
def leaderboard():
    """Get leaderboard data - FIXED to return proper array format"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.username, 
                   COUNT(hp.id) as total_picks, 
                   COUNT(CASE WHEN hp.is_correct = 1 THEN 1 END) as points
            FROM users u
            LEFT JOIN historical_picks hp ON u.id = hp.user_id
            GROUP BY u.id, u.username
            ORDER BY points DESC, total_picks ASC
        """)
        
        leaderboard_data = []
        for i, (username, total_picks, points) in enumerate(cursor.fetchall()):
            leaderboard_data.append({
                'rank': i + 1,
                'username': username,
                'points': points,
                'total_picks': total_picks,
                'correct_picks': points
            })
        
        conn.close()
        
        # Return GUARANTEED array format
        return jsonify({
            'success': True, 
            'leaderboard': leaderboard_data  # This MUST be an array
        })
        
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        return jsonify({'success': False, 'message': 'Fehler beim Laden des Leaderboards'}), 500

@app.route('/api/all-picks')
def all_picks():
    """Get all picks from all users - FIXED to return proper array format"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.username, hp.week, hp.team_name, 
                   CASE WHEN hp.is_correct = 1 THEN 'Correct' ELSE 'Incorrect' END as result,
                   hp.created_at
            FROM historical_picks hp
            JOIN users u ON hp.user_id = u.id
            ORDER BY hp.week, u.username
        """)
        
        all_picks_data = []
        for row in cursor.fetchall():
            all_picks_data.append({
                'user': row[0],
                'week': row[1],
                'team': row[2],
                'result': row[3],
                'created_at': row[4]
            })
        
        conn.close()
        
        # Return GUARANTEED array format
        return jsonify({
            'success': True, 
            'picks': all_picks_data  # This MUST be an array
        })
        
    except Exception as e:
        logger.error(f"All picks error: {e}")
        return jsonify({'success': False, 'message': 'Fehler beim Laden aller Picks'}), 500

@app.route('/api/available-weeks')
def available_weeks():
    """Get all available weeks W1-W18"""
    try:
        weeks_info = []
        for week in range(1, 19):  # W1-W18
            status = 'completed' if week <= 2 else 'active' if week == 3 else 'upcoming'
            weeks_info.append({
                'week': week,
                'status': status,
                'games_count': 16,
                'completed_games': 16 if week <= 2 else 0
            })
        
        return jsonify({
            'success': True,
            'weeks': weeks_info,
            'current_week': 3
        })
        
    except Exception as e:
        logger.error(f"Available weeks error: {e}")
        return jsonify({'success': False, 'message': 'Fehler beim Laden der verfügbaren Wochen'}), 500

@app.route('/api/matches')
def get_matches():
    """Get matches for a specific week with team graying logic"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Nicht angemeldet'}), 401

        user_id = session['user_id']
        week = request.args.get('week', type=int)

        if not week:
            return jsonify({'success': False, 'message': 'Woche nicht angegeben'}), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get matches for the week
        cursor.execute("""
            SELECT m.id, m.week, m.home_team_id, m.away_team_id, m.game_time, m.is_completed,
                   m.home_score, m.away_score,
                   ht.name as home_name, ht.abbreviation as home_abbr, ht.logo_url as home_logo,
                   at.name as away_name, at.abbreviation as away_abbr, at.logo_url as away_logo
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE m.week = ?
            ORDER BY m.game_time
        """, (week,))
        
        matches_data = []
        for row in cursor.fetchall():
            # Convert game time to Vienna timezone
            game_time = datetime.fromisoformat(row[4])
            if game_time.tzinfo is None:
                game_time = VIENNA_TZ.localize(game_time)
            else:
                game_time = game_time.astimezone(VIENNA_TZ)
            
            matches_data.append({
                'id': row[0],
                'week': row[1],
                'home_team': {'id': row[2], 'name': row[8], 'abbr': row[9], 'logo_url': row[10]},
                'away_team': {'id': row[3], 'name': row[11], 'abbr': row[12], 'logo_url': row[13]},
                'game_time': game_time.isoformat(),
                'is_completed': bool(row[5]),
                'home_score': row[6],
                'away_score': row[7]
            })
        
        # Get user picks for this week
        cursor.execute("SELECT match_id, team_id FROM picks WHERE user_id = ? AND week = ?", (user_id, week))
        picks_data = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get team usage for graying logic
        cursor.execute("SELECT team_id, usage_type FROM team_usage WHERE user_id = ?", (user_id,))
        team_usage = cursor.fetchall()
        
        # Calculate unpickable teams
        used_loser_teams = {row[0] for row in team_usage if row[1] == 'loser'}
        winner_usage_counts = {}
        for team_id, usage_type in team_usage:
            if usage_type == 'winner':
                winner_usage_counts[team_id] = winner_usage_counts.get(team_id, 0) + 1
        
        unpickable_teams = used_loser_teams.copy()
        for team_id, count in winner_usage_counts.items():
            if count >= 2:  # Max 2 times as winner
                unpickable_teams.add(team_id)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'matches': matches_data,
            'picks': picks_data,
            'unpickable_teams': list(unpickable_teams)
        })

    except Exception as e:
        logger.error(f"Error getting matches: {e}")
        return jsonify({'success': False, 'message': 'Fehler beim Laden der Spiele'}), 500

@app.route('/api/picks', methods=['POST'])
def save_pick():
    """Save user pick with validation"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Nicht angemeldet'}), 401

        data = request.get_json()
        user_id = session['user_id']
        match_id = data.get('match_id')
        team_id = data.get('team_id')
        week = data.get('week')

        if not all([match_id, team_id, week]):
            return jsonify({'success': False, 'message': 'Fehlende Daten für die Auswahl'}), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if game has started
        cursor.execute("SELECT game_time FROM matches WHERE id = ?", (match_id,))
        game_time_str = cursor.fetchone()[0]
        game_time = datetime.fromisoformat(game_time_str)
        if game_time.tzinfo is None:
            game_time = VIENNA_TZ.localize(game_time)
        
        if datetime.now(VIENNA_TZ) > game_time:
            conn.close()
            return jsonify({'success': False, 'message': 'Das Spiel hat bereits begonnen'}), 403

        # Check team usage limits
        cursor.execute("SELECT usage_type FROM team_usage WHERE user_id = ? AND team_id = ?", (user_id, team_id))
        usage_records = cursor.fetchall()
        
        loser_usage = any(record[0] == 'loser' for record in usage_records)
        winner_usage_count = sum(1 for record in usage_records if record[0] == 'winner')
        
        if loser_usage:
            conn.close()
            return jsonify({'success': False, 'message': 'Team bereits als Verlierer verwendet'}), 400
        
        if winner_usage_count >= 2:
            conn.close()
            return jsonify({'success': False, 'message': 'Team bereits 2x als Gewinner verwendet'}), 400

        # Save or update pick
        cursor.execute("SELECT id FROM picks WHERE user_id = ? AND week = ?", (user_id, week))
        existing_pick = cursor.fetchone()
        
        if existing_pick:
            cursor.execute("""
                UPDATE picks SET match_id = ?, team_id = ?, created_at = ?
                WHERE user_id = ? AND week = ?
            """, (match_id, team_id, datetime.now().isoformat(), user_id, week))
        else:
            cursor.execute("""
                INSERT INTO picks (user_id, match_id, team_id, week, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, match_id, team_id, week, datetime.now().isoformat()))
        
        # Update team usage
        cursor.execute("DELETE FROM team_usage WHERE user_id = ? AND week = ?", (user_id, week))
        cursor.execute("""
            INSERT INTO team_usage (user_id, team_id, usage_type, week, created_at)
            VALUES (?, ?, 'winner', ?, ?)
        """, (user_id, team_id, week, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Pick erfolgreich gespeichert'})

    except Exception as e:
        logger.error(f"Error saving pick: {e}")
        return jsonify({'success': False, 'message': 'Fehler beim Speichern des Picks'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
