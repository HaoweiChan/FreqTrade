#!/usr/bin/env python3
"""
Simple backtest runner without multiprocessing for DB compatibility.
"""

import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest_db import init_backtest_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_single_backtest(strategy_name: str, config_path: str, start_date: str, end_date: str):
    """Run a single backtest and save to DB."""
    
    # Initialize DB
    db = init_backtest_db()
    
    # Check if already exists
    if db.strategy_exists(strategy_name, start_date, end_date):
        logger.info(f"✅ {strategy_name} already has results for this timerange")
        return
    
    # Create run entry
    config = {
        'start_date': start_date,
        'end_date': end_date,
        'config_path': config_path
    }
    run_id = db.create_run(strategy_name, config)
    db.update_run_status(run_id, 'RUNNING')
    
    # Run backtest
    docker_image = "ghcr.io/haoweichan/freqtrade/freqtrade-bot:latest"
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{os.getcwd()}/user_data:/freqtrade/user_data",
        docker_image,
        "backtesting",
        "--config", config_path,
        "--strategy", strategy_name,
        "--timerange", f"{start_date}-{end_date}",
        "--timeframe", "5m"
    ]
    
    logger.info(f"🔄 Running backtest for {strategy_name}...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        end_time = time.time()
        
        if result.returncode == 0:
            # Parse output for basic metrics
            metrics = parse_output(result.stdout, strategy_name)
            metrics['execution_time'] = end_time - start_time
            
            # Save to DB
            metadata = {
                'execution_time': metrics.get('execution_time'),
                'detected_timeframe': '5m'
            }
            db.save_success_result(run_id, metrics, metadata)
            logger.info(f"✅ {strategy_name} completed in {end_time - start_time:.1f}s")
        else:
            db.save_failed_result(run_id, result.stderr, result.stdout)
            logger.error(f"❌ {strategy_name} failed: {result.stderr[:200]}")
            
    except subprocess.TimeoutExpired:
        db.save_failed_result(run_id, "Timeout after 300s")
        logger.error(f"⏰ {strategy_name} timed out")
    except Exception as e:
        db.save_failed_result(run_id, str(e))
        logger.error(f"💥 {strategy_name} error: {e}")


def parse_output(output: str, strategy_name: str) -> dict:
    """Parse freqtrade output for key metrics."""
    metrics = {
        'strategy': strategy_name,
        'total_return': 0.0,
        'total_trades': 0,
        'win_rate': 0.0,
        'profit_factor': 0.0,
        'sharpe_ratio': 0.0,
        'max_drawdown': 0.0,
        'total_profit_percent': 0.0
    }
    
    lines = output.split('\n')
    
    for line in lines:
        if '│' in line:
            parts = [p.strip() for p in line.split('│')]
            
            if len(parts) >= 4:
                if 'Total profit %' in parts[1]:
                    try:
                        metrics['total_profit_percent'] = float(parts[2].replace('%', ''))
                    except:
                        pass
                elif 'Sharpe' in parts[1]:
                    try:
                        metrics['sharpe_ratio'] = float(parts[2])
                    except:
                        pass
                elif 'Profit factor' in parts[1]:
                    try:
                        metrics['profit_factor'] = float(parts[2])
                    except:
                        pass
        
        # Parse strategy summary
        if strategy_name in line and '│' in line:
            parts = [p.strip() for p in line.split('│')]
            if len(parts) >= 9:
                try:
                    metrics['total_trades'] = int(parts[2])
                    metrics['total_profit_percent'] = float(parts[5])
                    win_stats = parts[7].split()
                    if len(win_stats) >= 4:
                        metrics['win_rate'] = float(win_stats[3])
                except:
                    pass
    
    return metrics


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategies", nargs="+", required=True)
    parser.add_argument("--config", default="user_data/config.json")
    parser.add_argument("--timerange", required=True)
    
    args = parser.parse_args()
    
    start_date, end_date = args.timerange.split('-')
    
    for strategy in args.strategies:
        run_single_backtest(strategy, args.config, start_date, end_date)
    
    logger.info("✅ All backtests complete!")
