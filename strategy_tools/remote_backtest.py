#!/usr/bin/env python3
"""
Remote backtest runner using Ray and Docker.
Run this on the remote server to execute backtests.
"""

import os
import sys
import time
import subprocess
import logging
from typing import Dict, List

import ray

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@ray.remote
def run_backtest_docker(
    strategy_name: str,
    start_date: str,
    end_date: str,
    timeframe: str = "5m",
    timeout: int = 300
) -> Dict:
    """Run a single backtest using Docker."""
    import subprocess
    import time
    
    freqtrade_dir = "/home/willy/freqtrade"
    docker_image = "freqtradeorg/freqtrade:stable"
    
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{freqtrade_dir}/user_data:/freqtrade/user_data",
        docker_image,
        "backtesting",
        "--config", "user_data/config.json",
        "--strategy", strategy_name,
        "--timerange", f"{start_date}-{end_date}",
        "--timeframe", timeframe,
    ]
    
    start_time = time.time()
    logger.info(f"🔄 Running backtest for {strategy_name}...")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            metrics = parse_output(result.stdout, strategy_name)
            return {
                'status': 'SUCCESS',
                'strategy': strategy_name,
                'metrics': metrics,
                'execution_time': execution_time,
            }
        else:
            return {
                'status': 'FAILED',
                'strategy': strategy_name,
                'error': result.stderr[:500],
                'execution_time': execution_time,
            }
            
    except subprocess.TimeoutExpired:
        return {
            'status': 'TIMEOUT',
            'strategy': strategy_name,
            'error': f'Timeout after {timeout}s',
            'execution_time': timeout,
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'strategy': strategy_name,
            'error': str(e),
            'execution_time': time.time() - start_time,
        }


def parse_output(output: str, strategy_name: str) -> Dict:
    """Parse freqtrade output for key metrics."""
    metrics = {
        'total_return': 0.0,
        'total_trades': 0,
        'win_rate': 0.0,
        'profit_factor': 0.0,
        'sharpe_ratio': 0.0,
    }
    
    for line in output.split('\n'):
        if '│' in line:
            parts = [p.strip() for p in line.split('│')]
            if len(parts) >= 3:
                if 'Total profit %' in parts[1]:
                    try:
                        metrics['total_return'] = float(parts[2].replace('%', ''))
                    except:
                        pass
                elif 'Sharpe' in parts[1]:
                    try:
                        metrics['sharpe_ratio'] = float(parts[2])
                    except:
                        pass
        
        if strategy_name in line and '│' in line:
            parts = [p.strip() for p in line.split('│')]
            if len(parts) >= 9:
                try:
                    metrics['total_trades'] = int(parts[2])
                    metrics['total_return'] = float(parts[5])
                except:
                    pass
    
    return metrics


def run_backtests(strategies: List[str], start_date: str, end_date: str):
    """Run multiple backtests on Ray cluster."""
    ray.init(address="auto", ignore_reinit_error=True)
    
    logger.info(f"🚀 Submitting {len(strategies)} backtests to Ray...")
    
    futures = [
        run_backtest_docker.remote(s, start_date, end_date)
        for s in strategies
    ]
    
    results = []
    while futures:
        done, futures = ray.wait(futures, num_returns=1)
        for future in done:
            result = ray.get(future)
            results.append(result)
            
            emoji = "✅" if result['status'] == 'SUCCESS' else "❌"
            logger.info(f"{emoji} {result['strategy']}: {result['status']}")
            if result['status'] == 'SUCCESS':
                logger.info(f"   Return: {result['metrics'].get('total_return', 0):.2f}%")
    
    return results


if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategies", nargs="+", required=True)
    parser.add_argument("--timerange", required=True, help="YYYYMMDD-YYYYMMDD")
    parser.add_argument("--output", default="backtest_results.json")
    
    args = parser.parse_args()
    start_date, end_date = args.timerange.split('-')
    
    results = run_backtests(args.strategies, start_date, end_date)
    
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"💾 Results saved to {args.output}")
    
    # Summary
    successes = [r for r in results if r['status'] == 'SUCCESS']
    logger.info(f"\n📊 Summary: {len(successes)}/{len(results)} successful")
    for r in sorted(successes, key=lambda x: x['metrics'].get('total_return', 0), reverse=True):
        logger.info(f"   {r['strategy']}: {r['metrics'].get('total_return', 0):.2f}%")
