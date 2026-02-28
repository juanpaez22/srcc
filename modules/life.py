"""
Life Tracking Module - Plugin-style module for personal metrics
Handles: fitness, mood, learning, social tracking
"""

import os
import json
from datetime import datetime, timedelta
from flask import jsonify, request

# File paths
LIFE_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'life.json')

def load_life_data():
    """Load personal life tracking data (fitness, mood, learning, social)"""
    if os.path.exists(LIFE_FILE):
        try:
            with open(LIFE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'version': '1.0',
        'fitness': {'workouts': [], 'goals': {'weekly_gym_target': 4, 'primary': 'Build strength and muscle mass'}},
        'mood': {'entries': []},
        'learning': {'books': [], 'courses': [], 'skills': []},
        'social': {'interactions': []}
    }

def save_life_data(data):
    """Save personal life tracking data"""
    os.makedirs(os.path.dirname(LIFE_FILE), exist_ok=True)
    with open(LIFE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_streak(workouts, target=4):
    """Calculate current streak and weekly progress for gym/working out.
    target: workouts per week for streak
    Returns: {current_streak, weekly_count, weekly_target, weekly_progress_pct}"""
    if not workouts:
        return {'current_streak': 0, 'weekly_count': 0, 'weekly_target': target, 'weekly_progress_pct': 0}
    
    # Get dates of last 7 days
    today = datetime.now().date()
    week_dates = [(today - timedelta(days=i)).isoformat() for i in range(7)]
    
    # Count this week's workouts
    week_count = sum(1 for w in workouts if w.get('date', '')[:10] in week_dates)
    
    # Calculate streak - count consecutive days going backwards from today
    streak = 0
    check_date = today
    workout_dates = set(w.get('date', '')[:10] for w in workouts)
    
    while True:
        date_str = check_date.isoformat()
        if date_str in workout_dates:
            streak += 1
            check_date -= timedelta(days=1)
        elif check_date == today:
            # Today doesn't count yet, check yesterday
            check_date -= timedelta(days=1)
        else:
            break
        if streak > 365:  # Safety limit
            break
    
    return {
        'current_streak': streak,
        'weekly_count': week_count,
        'weekly_target': target,
        'weekly_progress_pct': min(100, int(week_count / target * 100))
    }

def calculate_achievements(workouts):
    """Calculate achievements/badges based on workout history.
    Returns list of unlocked achievements with details."""
    if not workouts:
        return []
    
    achievements = []
    total_workouts = len(workouts)
    
    # Get unique dates
    workout_dates = sorted(set(w.get('date', '')[:10] for w in workouts), reverse=True)
    
    # Calculate longest streak
    longest_streak = 0
    current_streak = 0
    prev_date = None
    
    for d in workout_dates:
        if prev_date:
            diff = (prev_date - datetime.strptime(d, '%Y-%m-%d').date()).days
            if diff == 1:
                current_streak += 1
            else:
                longest_streak = max(longest_streak, current_streak)
                current_streak = 1
        else:
            current_streak = 1
        prev_date = datetime.strptime(d, '%Y-%m-%d').date()
    longest_streak = max(longest_streak, current_streak)
    
    # Achievement definitions
    badges = [
        {'id': 'first_workout', 'name': 'First Step', 'desc': 'Completed your first workout', 'icon': '🌱', 'condition': total_workouts >= 1},
        {'id': 'five_workouts', 'name': 'Getting Started', 'desc': 'Completed 5 workouts', 'icon': '💪', 'condition': total_workouts >= 5},
        {'id': 'ten_workouts', 'name': 'Consistent', 'desc': 'Completed 10 workouts', 'icon': '🔥', 'condition': total_workouts >= 10},
        {'id': 'twenty_workouts', 'name': 'Dedicated', 'desc': 'Completed 20 workouts', 'icon': '⭐', 'condition': total_workouts >= 20},
        {'id': 'fifty_workouts', 'name': 'Beast Mode', 'desc': 'Completed 50 workouts', 'icon': '🦍', 'condition': total_workouts >= 50},
        {'id': 'streak_3', 'name': '3-Day Streak', 'desc': '3 days in a row', 'icon': '🎯', 'condition': longest_streak >= 3},
        {'id': 'streak_7', 'name': 'Week Warrior', 'desc': '7 days in a row', 'icon': '🗓️', 'condition': longest_streak >= 7},
        {'id': 'streak_14', 'name': 'Fortnight Fighter', 'desc': '14 days in a row', 'icon': '🛡️', 'condition': longest_streak >= 14},
        {'id': 'streak_30', 'name': 'Monthly Master', 'desc': '30 days in a row', 'icon': '👑', 'condition': longest_streak >= 30},
    ]
    
    for badge in badges:
        if badge['condition']:
            achievements.append({
                'id': badge['id'],
                'name': badge['name'],
                'desc': badge['desc'],
                'icon': badge['icon']
            })
    
    return {
        'achievements': achievements,
        'total_workouts': total_workouts,
        'longest_streak': longest_streak,
        'next_badge': next((b for b in badges if not b['condition']), None)
    }


def register_routes(app):
    """Register all life tracking routes with the Flask app"""
    
    @app.route('/life')
    def life():
        """Get all life data"""
        return load_life_data()

    @app.route('/life/fitness', methods=['GET', 'POST'])
    def life_fitness():
        """Log or get fitness data"""
        data = load_life_data()
        
        if request.method == 'POST':
            workout = {
                'date': request.json.get('date', datetime.now().strftime('%Y-%m-%d')),
                'type': request.json.get('type', 'gym'),
                'duration': request.json.get('duration'),
                'notes': request.json.get('notes', '')
            }
            data['fitness']['workouts'].append(workout)
            save_life_data(data)
            return jsonify({'success': True, 'workout': workout})
        
        return jsonify(data.get('fitness', {}))

    @app.route('/life/mood', methods=['GET', 'POST'])
    def life_mood():
        """Log or get mood data"""
        data = load_life_data()
        
        if request.method == 'POST':
            entry = {
                'date': request.json.get('date', datetime.now().strftime('%Y-%m-%d')),
                'mood': request.json.get('mood'),  # 1-10 scale
                'notes': request.json.get('notes', '')
            }
            data['mood']['entries'].append(entry)
            save_life_data(data)
            return jsonify({'success': True, 'entry': entry})
        
        return jsonify(data.get('mood', {}))

    @app.route('/life/learning', methods=['GET', 'POST'])
    def life_learning():
        """Log or get learning data"""
        data = load_life_data()
        
        if request.method == 'POST':
            item = {
                'date': request.json.get('date', datetime.now().strftime('%Y-%m-%d')),
                'type': request.json.get('type', 'book'),  # book, course, skill
                'title': request.json.get('title'),
                'notes': request.json.get('notes', '')
            }
            item_type = item['type'] + 's'  # books, courses, skills
            if item_type not in data['learning']:
                data['learning'][item_type] = []
            data['learning'][item_type].append(item)
            save_life_data(data)
            return jsonify({'success': True, 'item': item})
        
        return jsonify(data.get('learning', {}))

    @app.route('/life/social', methods=['GET', 'POST'])
    def life_social():
        """Log or get social data"""
        data = load_life_data()
        
        if request.method == 'POST':
            interaction = {
                'date': request.json.get('date', datetime.now().strftime('%Y-%m-%d')),
                'type': request.json.get('type', 'friend'),  # family, friend, colleague
                'with': request.json.get('with'),
                'notes': request.json.get('notes', '')
            }
            data['social']['interactions'].append(interaction)
            save_life_data(data)
            return jsonify({'success': True, 'interaction': interaction})
        
        return jsonify(data.get('social', {}))

    @app.route('/life/streaks')
    def life_streaks():
        """Get streak info for fitness and other tracked activities"""
        data = load_life_data()
        fitness = data.get('fitness', {})
        workouts = fitness.get('workouts', [])
        
        # Get weekly gym target (default 4)
        target = fitness.get('goals', {}).get('weekly_gym_target', 4)
        
        streak = calculate_streak(workouts, target)
        achievements = calculate_achievements(workouts)
        
        return jsonify({
            'fitness': streak,
            'achievements': achievements,
            'goals': fitness.get('goals', {})
        })

    @app.route('/log', methods=['POST'])
    def log_activity():
        """Parse natural language and log to appropriate life category.
        Gateway calls this for messages like 'I went to the gym', 'feeling great', etc."""
        text = (request.json.get('text', '') or '').lower()
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'})
        
        today = datetime.now().strftime('%Y-%m-%d')
        logged = []
        
        life = load_life_data()
        
        # Fitness keywords
        fitness_kw = ['gym', 'workout', 'lift', 'ran', 'run', 'soccer', 'tennis', 'exercise', 'training', 'push day', 'leg day']
        if any(kw in text for kw in fitness_kw):
            workout = {
                'date': today,
                'type': 'gym' if 'gym' in text or 'lift' in text else ('run' if 'run' in text else 'workout'),
                'duration': 60,  # default
                'notes': text[:100]
            }
            life['fitness']['workouts'].append(workout)
            logged.append(f"workout logged")
        
        # Mood keywords
        mood_kw = {'great': 9, 'good': 7, 'okay': 5, 'meh': 4, 'bad': 2, 'terrible': 1, 'awesome': 10, 'amazing': 10}
        for kw, val in mood_kw.items():
            if kw in text:
                entry = {'date': today, 'mood': val, 'notes': text[:100]}
                life['mood']['entries'].append(entry)
                logged.append(f"mood: {val}/10")
                break
        
        # Learning keywords
        learn_kw = ['read', 'book', 'course', 'learned', 'studied', 'article']
        if any(kw in text for kw in learn_kw):
            item = {'date': today, 'type': 'book' if 'book' in text else 'article', 'title': text[:50], 'notes': ''}
            if 'books' not in life['learning']:
                life['learning']['books'] = []
            life['learning']['books'].append(item)
            logged.append("learning item logged")
        
        # Social keywords
        social_kw = ['hung out', 'met', 'call', 'dinner', 'lunch', 'coffee', 'friend', 'family']
        if any(kw in text for kw in social_kw):
            interaction = {'date': today, 'type': 'friend', 'with': text[:30], 'notes': ''}
            life['social']['interactions'].append(interaction)
            logged.append("social interaction logged")
        
        if logged:
            save_life_data(life)
            
            # Build friendly response
            response_msg = "Got it! "
            
            if 'workout logged' in logged:
                # Calculate streak for workout
                streak_info = calculate_streak(life.get('fitness', {}).get('workouts', []))
                streak = streak_info.get('current_streak', 0)
                week_count = streak_info.get('weekly_count', 0)
                target = streak_info.get('weekly_target', 4)
                
                if streak > 0:
                    response_msg += f"🏋️ Workout recorded! 🔥 {streak}-day streak! ({week_count}/{target} this week) "
                else:
                    response_msg += f"🏋️ Workout recorded! ({week_count}/{target} this week) "
            
            if 'mood:' in str(logged):
                response_msg += "😊 Mood noted! "
            
            if 'learning item logged' in logged:
                response_msg += "📚 Learning logged! "
            
            if 'social interaction logged' in logged:
                response_msg += "👥 Social time recorded! "
            
            return jsonify({'success': True, 'logged': logged, 'message': response_msg.strip()})
        
        return jsonify({'success': False, 'message': "Didn't recognize that activity. Try: 'went to gym', 'feeling great', 'read a book', 'hung out with friend'"})
