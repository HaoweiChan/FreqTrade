"""
Ray executor for distributed backtest execution.
"""

import os
import sys
import time
import subprocess
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Ray import with fallback
try:
    import ray
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False
    logger.warning("Ray not installed. Distributed execution will not be available.")


def init_ray(address: str = None):
    """Initialize Ray connection."""
    if not RAY_AVAILABLE:
        raise ImportError("Ray is not installed. Install with: pip install 'ray[default]'")
    
    address = address or os.getenv('RAY_ADDRESS', 'local')
    
    if address == 'local':
        ray.init(ignore_reinit_error=True)
        logger.info("Started local Ray instance")
    else:
        ray.init(address=address, ignore_reinit_error=True)
        logger.info(f"Connected to Ray at {address}")


@ray.remote
def run_backtest_remote(
    strategy_name: str,
    config_path: str,
    start_date: str,
    end_date: str,
    timeframe: str = "5m",
    timeout: int = 300
) -> Dict:
    """
    Remote function to execute a backtest on a Ray worker.
    
    Returns a dictionary with results or error information.
    """
    import subprocess
    import time
    import re
    
    cmd = [
        sys.executable, "-m", "freqtrade", "backtesting",
        "--config", config_path,
        "--strategy", strategy_name,
        "--timerange", f"{start_date}-{end_date}",
        "--timeframe", timeframe,
    ]
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            # Parse basic metrics from stdout
            metrics = parse_backtest_stdout(result.stdout, strategy_name)
            
            return {
                'status': 'SUCCESS',
                'strategy': strategy_name,
                'metrics': metrics,
                'execution_time': execution_time,
                'stdout': result.stdout,
                'stderr': result.stderr,
            }
        else:
            return {
                'status': 'FAILED',
                'strategy': strategy_name,
                'error': result.stderr,
                'stdout': result.stdout,
                'execution_time': execution_time,
            }
            
    except subprocess.TimeoutExpired:
        return {
            'status': 'TIMEOUT',
            'strategy': strategy_name,
            'error': f'Timeout after {timeout} seconds',
            'execution_time': timeout,
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'strategy': strategy_name,
            'error': str(e),
            'execution_time': time.time() - start_time,
        }


def parse_backtest_stdout(output: str, strategy_name: str) -> Dict:
    """Parse key metrics from freqtrade backtest stdout."""
    metrics = {
        'total_return': 0.0,
        'total_trades': 0,
        'win_rate': 0.0,
        'profit_factor': 0.0,
        'sharpe_ratio': 0.0,
        'max_drawdown': 0.0,
    }
    
    lines = output.split('\n')
    
    for line in lines:
        if '│' in line:
            parts = [p.strip() for p in line.split('│')]
            
            if len(parts) >= 3:
                label = parts[1] if len(parts) > 1 else ''
                value = parts[2] if len(parts) > 2 else ''
                
                if 'Total profit %' in label:
                    try:
                        metrics['total_return'] = float(value.replace('%', ''))
                    except:
                        pass
                elif 'Sharpe' in label:
                    try:
                        metrics['sharpe_ratio'] = float(value)
                    except:
                        pass
                elif 'Profit factor' in label:
                    try:
                        metrics['profit_factor'] = float(value)
                    except:
                        pass
                elif 'Max % of account underwater' in label or 'Absolute Drawdown' in label:
                    try:
                        metrics['max_drawdown'] = float(value.replace('%', ''))
                    except:
                        pass
        
        # Parse strategy summary line
        if strategy_name in line and '│' in line:
            parts = [p.strip() for p in line.split('│')]
            if len(parts) >= 9:
                try:
                    metrics['total_trades'] = int(parts[2])
                    metrics['total_return'] = float(parts[5])
                    
                    # Parse win stats
                    win_stats = parts[7].split()
                    if len(win_stats) >= 4:
                        metrics['win_rate'] = float(win_stats[3])
                except:
                    pass
    
    return metrics


class RayBacktestExecutor:
    """Executor for running backtests on Ray cluster."""
    
    def __init__(self, ray_address: str = None):
        self.ray_address = ray_address or os.getenv('RAY_ADDRESS', 'local')
        self.initialized = False
    
    def ensure_initialized(self):
        """Ensure Ray is initialized."""
        if not self.initialized:
            init_ray(self.ray_address)
            self.initialized = True
    
    def submit_backtests(
        self,
        strategies: List[str],
        config_path: str,
        start_date: str,
        end_date: str,
        timeframe: str = "5m",
        timeout: int = 300
    ) -> List[Dict]:
        """
        Submit multiple backtests to Ray cluster and wait for results.
        
        Returns list of result dictionaries.
        """
        self.ensure_initialized()
        
        logger.info(f"Submitting {len(strategies)} backtests to Ray...")
        
        # Submit all tasks
        futures = [
            run_backtest_remote.remote(
                strategy_name=strategy,
                config_path=config_path,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe,
                timeout=timeout
            )
            for strategy in strategies
        ]
        
        # Collect results as they complete
        results = []
        while futures:
            done, futures = ray.wait(futures, num_returns=1)
            for future in done:
                try:
                    result = ray.get(future)
                    results.append(result)
                    
                    status_emoji = "✅" if result['status'] == 'SUCCESS' else "❌"
                    logger.info(f"{status_emoji} {result['strategy']}: {result['status']}")
                except Exception as e:
                    logger.error(f"Error getting result: {e}")
        
        return results


# Convenience function
def run_backtests_on_ray(
    strategies: List[str],
    config_path: str,
    start_date: str,
    end_date: str,
    ray_address: str = None,
    **kwargs
) -> List[Dict]:
    """
    Run backtests on Ray cluster.
    
    Args:
        strategies: List of strategy names
        config_path: Path to freqtrade config
        start_date: Start date (YYYYMMDD)
        end_date: End date (YYYYMMDD)
        ray_address: Ray cluster address (default: from env or 'local')
        **kwargs: Additional arguments passed to submit_backtests
    
    Returns:
        List of result dictionaries
    """
    executor = RayBacktestExecutor(ray_address)
    return executor.submit_backtests(
        strategies=strategies,
        config_path=config_path,
        start_date=start_date,
        end_date=end_date,
        **kwargs
    )
