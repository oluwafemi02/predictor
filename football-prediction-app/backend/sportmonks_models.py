from datetime import datetime
from models import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Index, UniqueConstraint

class SportMonksLeague(db.Model):
    """League data from SportMonks API"""
    __tablename__ = 'sportmonks_leagues'
    
    id = db.Column(db.Integer, primary_key=True)
    sportmonks_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100))
    logo_path = db.Column(db.String(500))
    type = db.Column(db.String(50))
    is_cup = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fixtures = db.relationship('SportMonksFixture', back_populates='league', lazy='dynamic')
    
    def __repr__(self):
        return f'<SportMonksLeague {self.name}>'

class SportMonksTeam(db.Model):
    """Team data from SportMonks API"""
    __tablename__ = 'sportmonks_teams'
    
    id = db.Column(db.Integer, primary_key=True)
    sportmonks_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    short_code = db.Column(db.String(10))
    country = db.Column(db.String(100))
    venue_id = db.Column(db.Integer)
    venue_name = db.Column(db.String(200))
    venue_city = db.Column(db.String(100))
    logo_path = db.Column(db.String(500))
    founded = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    home_fixtures = db.relationship('SportMonksFixture', foreign_keys='SportMonksFixture.home_team_id', back_populates='home_team')
    away_fixtures = db.relationship('SportMonksFixture', foreign_keys='SportMonksFixture.away_team_id', back_populates='away_team')
    
    def __repr__(self):
        return f'<SportMonksTeam {self.name}>'

class SportMonksFixture(db.Model):
    """Fixture/Match data from SportMonks API"""
    __tablename__ = 'sportmonks_fixtures'
    
    id = db.Column(db.Integer, primary_key=True)
    sportmonks_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    league_id = db.Column(db.Integer, db.ForeignKey('sportmonks_leagues.id'))
    season_id = db.Column(db.Integer)
    stage_id = db.Column(db.Integer)
    round_id = db.Column(db.Integer)
    home_team_id = db.Column(db.Integer, db.ForeignKey('sportmonks_teams.id'))
    away_team_id = db.Column(db.Integer, db.ForeignKey('sportmonks_teams.id'))
    
    # Match details
    status = db.Column(db.String(50))  # NS, LIVE, FT, etc.
    starting_at = db.Column(db.DateTime, nullable=False, index=True)
    minute = db.Column(db.Integer)
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    
    # Additional data
    venue_id = db.Column(db.Integer)
    referee_id = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    league = db.relationship('SportMonksLeague', back_populates='fixtures')
    home_team = db.relationship('SportMonksTeam', foreign_keys=[home_team_id], back_populates='home_fixtures')
    away_team = db.relationship('SportMonksTeam', foreign_keys=[away_team_id], back_populates='away_fixtures')
    predictions = db.relationship('SportMonksPrediction', back_populates='fixture', uselist=False)
    value_bets = db.relationship('SportMonksValueBet', back_populates='fixture')
    odds = db.relationship('SportMonksOdds', back_populates='fixture')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_fixture_date', 'starting_at'),
        Index('idx_fixture_status', 'status'),
        Index('idx_fixture_league_date', 'league_id', 'starting_at'),
    )
    
    def __repr__(self):
        return f'<SportMonksFixture {self.home_team.name if self.home_team else "?"} vs {self.away_team.name if self.away_team else "?"}>'

class SportMonksPrediction(db.Model):
    """AI Predictions from SportMonks API"""
    __tablename__ = 'sportmonks_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    fixture_id = db.Column(db.Integer, db.ForeignKey('sportmonks_fixtures.id'), unique=True)
    
    # Match outcome probabilities
    home_win_probability = db.Column(db.Float)
    draw_probability = db.Column(db.Float)
    away_win_probability = db.Column(db.Float)
    
    # Over/Under predictions
    over_25_probability = db.Column(db.Float)
    under_25_probability = db.Column(db.Float)
    over_15_probability = db.Column(db.Float)
    under_15_probability = db.Column(db.Float)
    over_35_probability = db.Column(db.Float)
    under_35_probability = db.Column(db.Float)
    
    # Both teams to score
    btts_yes_probability = db.Column(db.Float)
    btts_no_probability = db.Column(db.Float)
    
    # Correct score predictions (top 5)
    correct_scores = db.Column(JSON)  # Store as JSON array
    
    # Prediction confidence
    confidence_level = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fixture = db.relationship('SportMonksFixture', back_populates='predictions')
    
    def __repr__(self):
        return f'<SportMonksPrediction for fixture {self.fixture_id}>'

class SportMonksValueBet(db.Model):
    """Value Bet recommendations from SportMonks API"""
    __tablename__ = 'sportmonks_value_bets'
    
    id = db.Column(db.Integer, primary_key=True)
    fixture_id = db.Column(db.Integer, db.ForeignKey('sportmonks_fixtures.id'))
    
    # Bet details
    market = db.Column(db.String(50))  # 1X2, Over/Under, BTTS, etc.
    selection = db.Column(db.String(50))  # Home, Away, Draw, Over 2.5, etc.
    bookmaker = db.Column(db.String(100))
    
    # Value calculation
    predicted_probability = db.Column(db.Float)
    bookmaker_odds = db.Column(db.Float)
    implied_probability = db.Column(db.Float)
    value_percentage = db.Column(db.Float)  # How much value the bet has
    
    # Recommendation
    confidence = db.Column(db.Float)
    stake_suggestion = db.Column(db.Float)  # Suggested stake percentage
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    fixture = db.relationship('SportMonksFixture', back_populates='value_bets')
    
    # Index for performance
    __table_args__ = (
        Index('idx_value_bet_fixture', 'fixture_id'),
        Index('idx_value_bet_value', 'value_percentage'),
    )
    
    def __repr__(self):
        return f'<SportMonksValueBet {self.market} - {self.selection} ({self.value_percentage}%)>'

class SportMonksOdds(db.Model):
    """Bookmaker odds from SportMonks API"""
    __tablename__ = 'sportmonks_odds'
    
    id = db.Column(db.Integer, primary_key=True)
    fixture_id = db.Column(db.Integer, db.ForeignKey('sportmonks_fixtures.id'))
    bookmaker_id = db.Column(db.Integer)
    bookmaker_name = db.Column(db.String(100))
    
    # Market type
    market = db.Column(db.String(50))  # 1X2, Asian Handicap, Over/Under, etc.
    
    # Odds data (stored as JSON for flexibility)
    odds_data = db.Column(JSON)
    
    # Timestamps
    last_updated = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    fixture = db.relationship('SportMonksFixture', back_populates='odds')
    
    # Index for performance
    __table_args__ = (
        Index('idx_odds_fixture_bookmaker', 'fixture_id', 'bookmaker_id'),
    )
    
    def __repr__(self):
        return f'<SportMonksOdds {self.bookmaker_name} - {self.market}>'

class SportMonksLiveData(db.Model):
    """Live match data from SportMonks API"""
    __tablename__ = 'sportmonks_live_data'
    
    id = db.Column(db.Integer, primary_key=True)
    fixture_id = db.Column(db.Integer, db.ForeignKey('sportmonks_fixtures.id'), unique=True)
    
    # Live statistics
    home_possession = db.Column(db.Float)
    away_possession = db.Column(db.Float)
    home_shots = db.Column(db.Integer)
    away_shots = db.Column(db.Integer)
    home_shots_on_target = db.Column(db.Integer)
    away_shots_on_target = db.Column(db.Integer)
    home_corners = db.Column(db.Integer)
    away_corners = db.Column(db.Integer)
    home_yellow_cards = db.Column(db.Integer)
    away_yellow_cards = db.Column(db.Integer)
    home_red_cards = db.Column(db.Integer)
    away_red_cards = db.Column(db.Integer)
    
    # Events (goals, cards, substitutions)
    events = db.Column(JSON)
    
    # Live odds changes
    live_odds_changes = db.Column(JSON)
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SportMonksLiveData for fixture {self.fixture_id}>'

class SportMonksPlayer(db.Model):
    """Player data from SportMonks API"""
    __tablename__ = 'sportmonks_players'
    
    id = db.Column(db.Integer, primary_key=True)
    sportmonks_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    team_id = db.Column(db.Integer, db.ForeignKey('sportmonks_teams.id'))
    
    # Player details
    name = db.Column(db.String(200), nullable=False)
    display_name = db.Column(db.String(200))
    position = db.Column(db.String(50))
    number = db.Column(db.Integer)
    nationality = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    height = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    image_path = db.Column(db.String(500))
    
    # Performance stats (current season)
    appearances = db.Column(db.Integer, default=0)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SportMonksPlayer {self.name}>'

class SportMonksStanding(db.Model):
    """League standings from SportMonks API"""
    __tablename__ = 'sportmonks_standings'
    
    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('sportmonks_leagues.id'))
    season_id = db.Column(db.Integer)
    team_id = db.Column(db.Integer, db.ForeignKey('sportmonks_teams.id'))
    
    # Standing data
    position = db.Column(db.Integer)
    played = db.Column(db.Integer)
    won = db.Column(db.Integer)
    draw = db.Column(db.Integer)
    lost = db.Column(db.Integer)
    goals_for = db.Column(db.Integer)
    goals_against = db.Column(db.Integer)
    goal_difference = db.Column(db.Integer)
    points = db.Column(db.Integer)
    
    # Form
    recent_form = db.Column(db.String(10))  # e.g., "WWLDW"
    
    # Home/Away splits
    home_played = db.Column(db.Integer)
    home_won = db.Column(db.Integer)
    home_draw = db.Column(db.Integer)
    home_lost = db.Column(db.Integer)
    away_played = db.Column(db.Integer)
    away_won = db.Column(db.Integer)
    away_draw = db.Column(db.Integer)
    away_lost = db.Column(db.Integer)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('league_id', 'season_id', 'team_id', name='_league_season_team_uc'),
        Index('idx_standing_position', 'league_id', 'season_id', 'position'),
    )
    
    def __repr__(self):
        return f'<SportMonksStanding {self.position}. {self.team_id}>'