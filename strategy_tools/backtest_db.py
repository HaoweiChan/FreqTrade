"""
Database models and operations for backtest results storage.
Uses PostgreSQL via SQLAlchemy.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.sql import func
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

Base = declarative_base()


class BacktestRun(Base):
    """Model for storing backtest results."""
    __tablename__ = 'backtest_runs'

    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(255), nullable=False, index=True)
    status = Column(String(50), default='PENDING', index=True)  # PENDING, RUNNING, SUCCESS, FAILED
    
    # Core metrics
    total_return = Column(Float, nullable=True)
    total_trades = Column(Integer, nullable=True)
    win_rate = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    
    # Additional metrics
    winning_trades = Column(Integer, nullable=True)
    losing_trades = Column(Integer, nullable=True)
    avg_profit = Column(Float, nullable=True)
    avg_duration = Column(String(100), nullable=True)
    best_pair = Column(String(50), nullable=True)
    worst_pair = Column(String(50), nullable=True)
    total_profit_abs = Column(Float, nullable=True)
    market_change = Column(Float, nullable=True)
    
    # Execution metadata
    error_message = Column(Text, nullable=True)
    stdout = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)
    detected_timeframe = Column(String(20), nullable=True)
    freqtrade_version = Column(String(100), nullable=True)
    command_executed = Column(Text, nullable=True)
    
    # Config
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)
    config_path = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_strategy_status', 'strategy_name', 'status'),
        Index('idx_total_return', 'total_return'),
        Index('idx_created_at', 'created_at'),
    )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'strategy_name': self.strategy_name,
            'status': self.status,
            'total_return': self.total_return,
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'avg_profit': self.avg_profit,
            'avg_duration': self.avg_duration,
            'best_pair': self.best_pair,
            'worst_pair': self.worst_pair,
            'total_profit_abs': self.total_profit_abs,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'detected_timeframe': self.detected_timeframe,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class BacktestDB:
    """Database operations for backtest results."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'postgresql://localhost/freqtrade_backtest')
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def init_db(self):
        """Create all tables if they don't exist."""
        Base.metadata.create_all(self.engine)
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_run(self, strategy_name: str, config: Dict = None) -> int:
        """Create a new backtest run entry and return its ID."""
        with self.get_session() as session:
            run = BacktestRun(
                strategy_name=strategy_name,
                status='PENDING',
                start_date=config.get('start_date') if config else None,
                end_date=config.get('end_date') if config else None,
                config_path=config.get('config_path') if config else None,
            )
            session.add(run)
            session.flush()
            return run.id
    
    def update_run_status(self, run_id: int, status: str):
        """Update the status of a backtest run."""
        with self.get_session() as session:
            run = session.query(BacktestRun).filter_by(id=run_id).first()
            if run:
                run.status = status
    
    def save_success_result(self, run_id: int, metrics: Dict, metadata: Dict = None):
        """Save a successful backtest result."""
        with self.get_session() as session:
            run = session.query(BacktestRun).filter_by(id=run_id).first()
            if not run:
                return
            
            run.status = 'SUCCESS'
            
            # Core metrics
            run.total_return = metrics.get('total_profit_percent', 0.0)
            run.total_trades = metrics.get('total_trades', 0)
            run.win_rate = metrics.get('win_rate', 0.0)
            run.profit_factor = metrics.get('profit_factor', 0.0)
            run.sharpe_ratio = metrics.get('sharpe_ratio', 0.0)
            run.max_drawdown = metrics.get('max_drawdown', 0.0)
            
            # Additional metrics
            run.winning_trades = metrics.get('winning_trades', 0)
            run.losing_trades = metrics.get('losing_trades', 0)
            run.avg_profit = metrics.get('avg_profit', 0.0)
            run.avg_duration = metrics.get('avg_duration', '')
            run.best_pair = metrics.get('best_pair', '')
            run.worst_pair = metrics.get('worst_pair', '')
            run.total_profit_abs = metrics.get('total_profit_abs', 0.0)
            run.market_change = metrics.get('market_change', 0.0)
            
            # Metadata
            if metadata:
                run.execution_time = metadata.get('execution_time')
                run.detected_timeframe = metadata.get('detected_timeframe')
                run.freqtrade_version = metadata.get('freqtrade_version')
                run.command_executed = metadata.get('command_executed')
    
    def save_failed_result(self, run_id: int, error: str, stdout: str = None):
        """Save a failed backtest result."""
        with self.get_session() as session:
            run = session.query(BacktestRun).filter_by(id=run_id).first()
            if run:
                run.status = 'FAILED'
                run.error_message = error
                run.stdout = stdout
    
    def get_run(self, run_id: int) -> Optional[BacktestRun]:
        """Get a single backtest run by ID."""
        with self.get_session() as session:
            run = session.query(BacktestRun).filter_by(id=run_id).first()
            return run.to_dict() if run else None
    
    def get_latest_run_for_strategy(self, strategy_name: str) -> Optional[Dict]:
        """Get the most recent backtest run for a strategy."""
        with self.get_session() as session:
            run = session.query(BacktestRun)\
                .filter_by(strategy_name=strategy_name)\
                .order_by(BacktestRun.created_at.desc())\
                .first()
            return run.to_dict() if run else None
    
    def get_successful_strategies(self) -> List[str]:
        """Get list of strategies with successful backtests."""
        with self.get_session() as session:
            runs = session.query(BacktestRun.strategy_name)\
                .filter_by(status='SUCCESS')\
                .distinct()\
                .all()
            return [r[0] for r in runs]
    
    def get_all_results(self, status: str = None, limit: int = None) -> List[Dict]:
        """Get all backtest results, optionally filtered by status."""
        with self.get_session() as session:
            query = session.query(BacktestRun)
            
            if status:
                query = query.filter_by(status=status)
            
            query = query.order_by(BacktestRun.total_return.desc().nullslast())
            
            if limit:
                query = query.limit(limit)
            
            return [run.to_dict() for run in query.all()]
    
    def get_top_strategies(self, n: int = 20) -> List[Dict]:
        """Get top N strategies by total return."""
        with self.get_session() as session:
            runs = session.query(BacktestRun)\
                .filter_by(status='SUCCESS')\
                .order_by(BacktestRun.total_return.desc())\
                .limit(n)\
                .all()
            return [run.to_dict() for run in runs]
    
    def get_failed_strategies(self) -> List[Dict]:
        """Get all failed backtest runs."""
        with self.get_session() as session:
            runs = session.query(BacktestRun)\
                .filter_by(status='FAILED')\
                .order_by(BacktestRun.created_at.desc())\
                .all()
            return [run.to_dict() for run in runs]
    
    def strategy_exists(self, strategy_name: str, start_date: str, end_date: str) -> bool:
        """Check if a successful backtest exists for the given strategy and date range."""
        with self.get_session() as session:
            run = session.query(BacktestRun)\
                .filter_by(
                    strategy_name=strategy_name,
                    status='SUCCESS',
                    start_date=start_date,
                    end_date=end_date
                )\
                .first()
            return run is not None
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for all backtests."""
        with self.get_session() as session:
            total = session.query(func.count(BacktestRun.id)).scalar()
            successful = session.query(func.count(BacktestRun.id)).filter_by(status='SUCCESS').scalar()
            failed = session.query(func.count(BacktestRun.id)).filter_by(status='FAILED').scalar()
            pending = session.query(func.count(BacktestRun.id)).filter_by(status='PENDING').scalar()
            
            avg_return = session.query(func.avg(BacktestRun.total_return))\
                .filter_by(status='SUCCESS').scalar()
            
            best = session.query(BacktestRun)\
                .filter_by(status='SUCCESS')\
                .order_by(BacktestRun.total_return.desc())\
                .first()
            
            worst = session.query(BacktestRun)\
                .filter_by(status='SUCCESS')\
                .order_by(BacktestRun.total_return.asc())\
                .first()
            
            return {
                'total_runs': total,
                'successful': successful,
                'failed': failed,
                'pending': pending,
                'success_rate': (successful / total * 100) if total > 0 else 0,
                'avg_return': avg_return or 0,
                'best_strategy': best.strategy_name if best else None,
                'best_return': best.total_return if best else None,
                'worst_strategy': worst.strategy_name if worst else None,
                'worst_return': worst.total_return if worst else None,
            }


# Convenience function for quick initialization
def init_backtest_db(database_url: str = None) -> BacktestDB:
    """Initialize and return a BacktestDB instance."""
    db = BacktestDB(database_url)
    db.init_db()
    return db
