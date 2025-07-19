#!/usr/bin/env python3
"""
Strategy Backtest Status Checker
Shows which strategies have been completed, failed, or are pending.
"""

import json
from pathlib import Path
from datetime import datetime
import pandas as pd

class StrategyStatusChecker:
    def __init__(self):
        self.results_dir = Path("user_data/backtest_results")
        self.individual_results_dir = self.results_dir / "individual_results"
        
    def discover_all_strategies(self):
        """Discover all available strategies."""
        strategies_dir = Path("user_data/strategies")
        strategies = []
        
        for strategy_dir in strategies_dir.iterdir():
            if strategy_dir.is_dir() and not strategy_dir.name.startswith('.'):
                py_files = list(strategy_dir.glob("*.py"))
                if py_files:
                    strategies.append(strategy_dir.name)
        
        return sorted(strategies)
    
    def get_strategy_status(self):
        """Get status of all strategies."""
        all_strategies = self.discover_all_strategies()
        
        status_data = []
        
        for strategy in all_strategies:
            result_file = self.individual_results_dir / f"{strategy}_result.json"
            failed_file = self.individual_results_dir / f"{strategy}_failed.json"
            
            if result_file.exists():
                try:
                    with open(result_file, 'r') as f:
                        result = json.load(f)
                    
                    status_data.append({
                        'strategy': strategy,
                        'status': 'completed',
                        'total_profit_percent': result.get('total_profit_percent', 0),
                        'total_trades': result.get('total_trades', 0),
                        'win_rate': result.get('win_rate', 0),
                        'max_drawdown': result.get('max_drawdown', 0),
                        'execution_time': result.get('execution_time', 0),
                        'backtest_timestamp': result.get('backtest_timestamp', ''),
                        'timerange': f"{result.get('backtest_config', {}).get('start_date', '')}-{result.get('backtest_config', {}).get('end_date', '')}"
                    })
                except Exception as e:
                    status_data.append({
                        'strategy': strategy,
                        'status': 'error_reading_result',
                        'error': str(e)
                    })
            
            elif failed_file.exists():
                try:
                    with open(failed_file, 'r') as f:
                        failed_result = json.load(f)
                    
                    status_data.append({
                        'strategy': strategy,
                        'status': 'failed',
                        'error': failed_result.get('error', 'Unknown error'),
                        'failed_timestamp': failed_result.get('failed_timestamp', ''),
                        'timerange': f"{failed_result.get('backtest_config', {}).get('start_date', '')}-{failed_result.get('backtest_config', {}).get('end_date', '')}"
                    })
                except Exception as e:
                    status_data.append({
                        'strategy': strategy,
                        'status': 'error_reading_failed',
                        'error': str(e)
                    })
            
            else:
                status_data.append({
                    'strategy': strategy,
                    'status': 'pending',
                })
        
        return status_data
    
    def print_status_summary(self):
        """Print a summary of strategy statuses."""
        status_data = self.get_strategy_status()
        
        # Count by status
        status_counts = {}
        for item in status_data:
            status = item['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        total_strategies = len(status_data)
        
        print("🔍 STRATEGY BACKTEST STATUS SUMMARY")
        print("=" * 50)
        print(f"Total Strategies: {total_strategies}")
        print()
        
        for status, count in status_counts.items():
            percentage = (count / total_strategies) * 100
            emoji = {
                'completed': '✅',
                'failed': '❌',
                'pending': '⏳',
                'error_reading_result': '⚠️',
                'error_reading_failed': '⚠️'
            }.get(status, '❓')
            
            print(f"{emoji} {status.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        print("\n" + "=" * 50)
        
        # Show completed strategies performance
        completed = [item for item in status_data if item['status'] == 'completed']
        if completed:
            print("\n📈 TOP 10 PERFORMING COMPLETED STRATEGIES:")
            print("-" * 50)
            
            # Sort by profit percentage
            completed_sorted = sorted(completed, key=lambda x: x.get('total_profit_percent', 0), reverse=True)
            
            for i, strategy in enumerate(completed_sorted[:10], 1):
                profit = strategy.get('total_profit_percent', 0)
                trades = strategy.get('total_trades', 0)
                win_rate = strategy.get('win_rate', 0)
                
                print(f"{i:2d}. {strategy['strategy']:<30} | {profit:7.2f}% | {trades:3.0f} trades | {win_rate:5.1f}% win")
        
        # Show failed strategies
        failed = [item for item in status_data if item['status'] == 'failed']
        if failed and len(failed) <= 10:
            print(f"\n❌ FAILED STRATEGIES ({len(failed)}):")
            print("-" * 50)
            
            for strategy in failed:
                error = strategy.get('error', 'Unknown error')[:60]
                print(f"• {strategy['strategy']:<30} | {error}")
        
        # Show pending strategies
        pending = [item for item in status_data if item['status'] == 'pending']
        if pending:
            print(f"\n⏳ PENDING STRATEGIES ({len(pending)}):")
            print("-" * 50)
            
            # Show first 20
            for strategy in pending[:20]:
                print(f"• {strategy['strategy']}")
            
            if len(pending) > 20:
                print(f"• ... and {len(pending) - 20} more")
        
        return status_data
    
    def export_status_csv(self, filename=None):
        """Export status to CSV file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.results_dir / f"strategy_status_{timestamp}.csv"
        
        status_data = self.get_strategy_status()
        df = pd.DataFrame(status_data)
        df.to_csv(filename, index=False)
        print(f"\n📄 Status exported to: {filename}")
        return filename

def main():
    checker = StrategyStatusChecker()
    status_data = checker.print_status_summary()
    
    # Automatically export status to CSV
    try:
        checker.export_status_csv()
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main() 