#!/usr/bin/env python3
"""
FastAPI server for backtest results database.
Provides REST API endpoints to query and store backtest results.
"""

import os
import sys
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from backtest_db import init_backtest_db, BacktestRun

app = FastAPI(
    title="Backtest Results API",
    description="API for querying and storing backtest results",
    version="1.0.0"
)

# Enable CORS for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB
db = None


def get_db():
    global db
    if db is None:
        db = init_backtest_db()
    return db


# Pydantic models
class BacktestResult(BaseModel):
    id: int
    strategy_name: str
    status: str
    total_return: Optional[float] = None
    total_trades: Optional[int] = None
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    execution_time: Optional[float] = None
    created_at: Optional[str] = None


class BacktestResultCreate(BaseModel):
    strategy_name: str
    status: str
    metrics: dict
    execution_time: Optional[float] = None


class StatsResponse(BaseModel):
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    best_strategy: Optional[str] = None
    best_return: Optional[float] = None
    avg_return: Optional[float] = None


# Endpoints
@app.get("/")
async def root():
    return {"status": "ok", "service": "Backtest Results API"}


@app.get("/api/results", response_model=List[BacktestResult])
async def get_results(
    status: Optional[str] = Query(None, description="Filter by status (SUCCESS, FAILED)"),
    strategy: Optional[str] = Query(None, description="Filter by strategy name"),
    min_return: Optional[float] = Query(None, description="Minimum return filter"),
    limit: int = Query(100, description="Max results to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """Get list of backtest results with optional filters."""
    db = get_db()
    
    with db.get_session() as session:
        query = session.query(BacktestRun)
        
        if status:
            query = query.filter(BacktestRun.status == status)
        if strategy:
            query = query.filter(BacktestRun.strategy_name.ilike(f"%{strategy}%"))
        if min_return is not None:
            query = query.filter(BacktestRun.total_return >= min_return)
        
        query = query.order_by(BacktestRun.total_return.desc().nullslast())
        query = query.offset(offset).limit(limit)
        
        results = []
        for run in query.all():
            results.append(BacktestResult(
                id=run.id,
                strategy_name=run.strategy_name,
                status=run.status,
                total_return=run.total_return,
                total_trades=run.total_trades,
                win_rate=run.win_rate,
                profit_factor=run.profit_factor,
                sharpe_ratio=run.sharpe_ratio,
                max_drawdown=run.max_drawdown,
                execution_time=run.execution_time,
                created_at=run.created_at.isoformat() if run.created_at else None
            ))
        
        return results


@app.get("/api/results/{run_id}", response_model=BacktestResult)
async def get_result(run_id: int):
    """Get a single backtest result by ID."""
    db = get_db()
    
    with db.get_session() as session:
        run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Result not found")
        
        return BacktestResult(
            id=run.id,
            strategy_name=run.strategy_name,
            status=run.status,
            total_return=run.total_return,
            total_trades=run.total_trades,
            win_rate=run.win_rate,
            profit_factor=run.profit_factor,
            sharpe_ratio=run.sharpe_ratio,
            max_drawdown=run.max_drawdown,
            execution_time=run.execution_time,
            created_at=run.created_at.isoformat() if run.created_at else None
        )


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get summary statistics."""
    db = get_db()
    
    with db.get_session() as session:
        total = session.query(BacktestRun).count()
        successful = session.query(BacktestRun).filter(BacktestRun.status == 'SUCCESS').count()
        failed = total - successful
        
        # Best strategy
        best = session.query(BacktestRun)\
            .filter(BacktestRun.status == 'SUCCESS')\
            .order_by(BacktestRun.total_return.desc())\
            .first()
        
        # Average return
        from sqlalchemy import func
        avg_return = session.query(func.avg(BacktestRun.total_return))\
            .filter(BacktestRun.status == 'SUCCESS')\
            .scalar()
        
        return StatsResponse(
            total_runs=total,
            successful_runs=successful,
            failed_runs=failed,
            success_rate=successful / total * 100 if total > 0 else 0,
            best_strategy=best.strategy_name if best else None,
            best_return=best.total_return if best else None,
            avg_return=avg_return
        )


@app.post("/api/results", response_model=BacktestResult)
async def create_result(result: BacktestResultCreate):
    """Save a new backtest result."""
    db = get_db()
    
    config = {'source': 'api'}
    run_id = db.create_run(result.strategy_name, config)
    
    if result.status == 'SUCCESS':
        db.save_success_result(run_id, result.metrics, {'execution_time': result.execution_time})
    else:
        db.save_failed_result(run_id, str(result.metrics.get('error', 'Unknown error')))
    
    # Return the created result
    with db.get_session() as session:
        run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
        return BacktestResult(
            id=run.id,
            strategy_name=run.strategy_name,
            status=run.status,
            total_return=run.total_return,
            total_trades=run.total_trades,
            win_rate=run.win_rate,
            profit_factor=run.profit_factor,
            sharpe_ratio=run.sharpe_ratio,
            max_drawdown=run.max_drawdown,
            execution_time=run.execution_time,
            created_at=run.created_at.isoformat() if run.created_at else None
        )


@app.get("/api/strategies")
async def get_strategies():
    """Get list of unique strategy names."""
    db = get_db()
    
    with db.get_session() as session:
        from sqlalchemy import distinct
        strategies = session.query(distinct(BacktestRun.strategy_name))\
            .order_by(BacktestRun.strategy_name)\
            .all()
        return [s[0] for s in strategies]


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Backtest Results API on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)
