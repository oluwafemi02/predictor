from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    code = db.Column(db.String(10))
    logo_url = db.Column(db.String(255))
    stadium = db.Column(db.String(100))
    founded = db.Column(db.Integer)
    
    # Relationships
    home_matches = db.relationship('Match', backref='home_team', foreign_keys='Match.home_team_id')
    away_matches = db.relationship('Match', backref='away_team', foreign_keys='Match.away_team_id')
    players = db.relationship('Player', backref='team')
    statistics = db.relationship('TeamStatistics', backref='team')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Player(db.Model):
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50))
    jersey_number = db.Column(db.Integer)
    age = db.Column(db.Integer)
    nationality = db.Column(db.String(50))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    photo_url = db.Column(db.String(255))
    
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    
    # Relationships
    injuries = db.relationship('Injury', backref='player')
    performances = db.relationship('PlayerPerformance', backref='player')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    
    match_date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(100))
    competition = db.Column(db.String(100))
    season = db.Column(db.String(20))
    round = db.Column(db.String(50))
    
    # Match results
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    home_score_halftime = db.Column(db.Integer)
    away_score_halftime = db.Column(db.Integer)
    
    # Match status
    status = db.Column(db.String(20))  # scheduled, in_play, finished, postponed
    referee = db.Column(db.String(100))
    attendance = db.Column(db.Integer)
    
    # Predictions
    predictions = db.relationship('Prediction', backref='match')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Injury(db.Model):
    __tablename__ = 'injuries'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    
    injury_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    expected_return_date = db.Column(db.Date)
    actual_return_date = db.Column(db.Date)
    severity = db.Column(db.String(20))  # minor, moderate, severe
    status = db.Column(db.String(20))  # active, recovered
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TeamStatistics(db.Model):
    __tablename__ = 'team_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    season = db.Column(db.String(20), nullable=False)
    competition = db.Column(db.String(100))
    
    # General statistics
    matches_played = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    
    # Goals
    goals_for = db.Column(db.Integer, default=0)
    goals_against = db.Column(db.Integer, default=0)
    clean_sheets = db.Column(db.Integer, default=0)
    
    # Form (last 5 matches)
    form = db.Column(db.String(5))  # e.g., "WWDLW"
    
    # Advanced stats
    possession_avg = db.Column(db.Float)
    shots_per_game = db.Column(db.Float)
    shots_on_target_per_game = db.Column(db.Float)
    passes_per_game = db.Column(db.Float)
    pass_accuracy = db.Column(db.Float)
    
    # Home/Away specific
    home_wins = db.Column(db.Integer, default=0)
    home_draws = db.Column(db.Integer, default=0)
    home_losses = db.Column(db.Integer, default=0)
    away_wins = db.Column(db.Integer, default=0)
    away_draws = db.Column(db.Integer, default=0)
    away_losses = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PlayerPerformance(db.Model):
    __tablename__ = 'player_performances'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    
    # Performance metrics
    minutes_played = db.Column(db.Integer)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    shots = db.Column(db.Integer, default=0)
    shots_on_target = db.Column(db.Integer, default=0)
    passes = db.Column(db.Integer, default=0)
    pass_accuracy = db.Column(db.Float)
    tackles = db.Column(db.Integer, default=0)
    interceptions = db.Column(db.Integer, default=0)
    fouls = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    
    # Prediction outcomes
    home_win_probability = db.Column(db.Float)
    draw_probability = db.Column(db.Float)
    away_win_probability = db.Column(db.Float)
    
    # Score predictions
    predicted_home_score = db.Column(db.Float)
    predicted_away_score = db.Column(db.Float)
    
    # Betting odds predictions
    over_2_5_probability = db.Column(db.Float)
    under_2_5_probability = db.Column(db.Float)
    both_teams_score_probability = db.Column(db.Float)
    
    # Model metadata
    model_version = db.Column(db.String(50))
    confidence_score = db.Column(db.Float)
    
    # Factors considered
    factors = db.Column(db.JSON)  # Store various factors that influenced the prediction
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class HeadToHead(db.Model):
    __tablename__ = 'head_to_head'
    
    id = db.Column(db.Integer, primary_key=True)
    team1_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    team2_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    
    # Historical stats
    total_matches = db.Column(db.Integer, default=0)
    team1_wins = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)
    team2_wins = db.Column(db.Integer, default=0)
    team1_goals = db.Column(db.Integer, default=0)
    team2_goals = db.Column(db.Integer, default=0)
    
    # Recent form
    last_5_results = db.Column(db.JSON)  # Store recent match results
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)