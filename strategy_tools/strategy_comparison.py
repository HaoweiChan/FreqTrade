#!/usr/bin/env python3
"""
Strategy Comparison Tool - Analyze backtested results and find top performers
This script crawls existing backtest results and generates comparison reports.
"""

import json
import pandas as pd
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging
import zipfile
import tempfile
import sys
import os

# Import shared utilities
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
import utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StrategyComparison:
    def __init__(self, results_dir: str = "user_data/backtest_results"):
        self.results_dir = Path(results_dir)
        self.individual_results_dir = self.results_dir / "individual_results"
        self.results = {}
        self.failed_strategies = []
        
        # Initialize shared utilities
        self.utils = utils.StrategyResultsUtils(results_dir)
        

    
    def collect_all_results(self):
        """Collect all existing results from strategy directories."""
        # Use shared utilities for consistent result detection
        self.results, self.failed_strategies = self.utils.collect_all_results()
    
    def generate_comparison_report(self, top_n: int = 20):
        """Generate a comprehensive comparison report."""
        if not self.results:
            logger.error("❌ No successful results found to compare!")
            return
        
        # Convert results to DataFrame for easier analysis
        df = pd.DataFrame(list(self.results.values()))
        
        # Sort by total profit percentage (descending)
        df = df.sort_values('total_profit_percent', ascending=False)
        
        # Generate timestamp for report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure results directory exists
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Save detailed CSV report
        csv_file = self.results_dir / f"strategy_comparison_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        logger.info(f"📄 Detailed CSV report saved: {csv_file}")
        
        # 2. Generate summary report
        self.generate_summary_report(df, timestamp)
        
        # 3. Generate top performers report
        self.generate_top_performers_report(df, timestamp, top_n)
        
        # 4. Save failed strategies report
        if self.failed_strategies:
            failed_file = self.results_dir / f"failed_strategies_{timestamp}.json"
            with open(failed_file, 'w') as f:
                json.dump(self.failed_strategies, f, indent=2)
            logger.info(f"❌ Failed strategies report saved: {failed_file}")
        
        logger.info(f"✅ All reports generated in: {self.results_dir}")
        
        # Display top performers summary
        self.display_top_performers_summary(df, top_n)
    
    def generate_summary_report(self, df: pd.DataFrame, timestamp: str):
        """Generate a summary statistics report."""
        summary_file = self.results_dir / f"summary_report_{timestamp}.txt"
        
        # Get backtest configuration from first result
        first_result = list(self.results.values())[0] if self.results else {}
        start_date = first_result.get('backtest_start', 'Unknown')
        end_date = first_result.get('backtest_end', 'Unknown')
        
        with open(summary_file, 'w') as f:
            f.write("FREQTRADE STRATEGY BACKTESTING SUMMARY REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Test Period: {start_date} to {end_date}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"OVERVIEW:\n")
            f.write(f"Total Strategies Tested: {len(df) + len(self.failed_strategies)}\n")
            f.write(f"Successful Backtests: {len(df)}\n")
            f.write(f"Failed Backtests: {len(self.failed_strategies)}\n")
            f.write(f"Success Rate: {(len(df)/(len(df) + len(self.failed_strategies)))*100:.1f}%\n\n")
            
            if len(df) > 0:
                f.write(f"PERFORMANCE STATISTICS:\n")
                f.write(f"Best Strategy: {df.iloc[0]['strategy']} ({df.iloc[0]['total_profit_percent']:.2f}%)\n")
                f.write(f"Worst Strategy: {df.iloc[-1]['strategy']} ({df.iloc[-1]['total_profit_percent']:.2f}%)\n")
                f.write(f"Average Return: {df['total_profit_percent'].mean():.2f}%\n")
                f.write(f"Median Return: {df['total_profit_percent'].median():.2f}%\n")
                f.write(f"Standard Deviation: {df['total_profit_percent'].std():.2f}%\n\n")
                
                f.write(f"PROFITABLE STRATEGIES:\n")
                profitable = df[df['total_profit_percent'] > 0]
                f.write(f"Count: {len(profitable)} ({(len(profitable)/len(df))*100:.1f}%)\n")
                if len(profitable) > 0:
                    f.write(f"Average Profit: {profitable['total_profit_percent'].mean():.2f}%\n\n")
                
                f.write(f"TRADING ACTIVITY:\n")
                f.write(f"Average Trades per Strategy: {df['total_trades'].mean():.1f}\n")
                f.write(f"Average Win Rate: {df['win_rate'].mean():.1f}%\n")
                f.write(f"Average Max Drawdown: {df['max_drawdown'].mean():.2f}%\n\n")
                
                # Additional metrics if available
                if 'sharpe_ratio' in df.columns:
                    f.write(f"RISK METRICS:\n")
                    f.write(f"Average Sharpe Ratio: {df['sharpe_ratio'].mean():.2f}\n")
                    f.write(f"Average Profit Factor: {df['profit_factor'].mean():.2f}\n")
                    if 'cagr' in df.columns:
                        f.write(f"Average CAGR: {df['cagr'].mean():.2f}%\n")
                    if 'sortino' in df.columns:
                        f.write(f"Average Sortino Ratio: {df['sortino'].mean():.2f}\n")
        
        logger.info(f"📊 Summary report saved: {summary_file}")
    
    def generate_top_performers_report(self, df: pd.DataFrame, timestamp: str, top_n: int = 20):
        """Generate a report of top performing strategies."""
        top_file = self.results_dir / f"top_{top_n}_strategies_{timestamp}.txt"
        
        with open(top_file, 'w') as f:
            f.write(f"TOP {top_n} PERFORMING STRATEGIES\n")
            f.write("=" * 50 + "\n\n")
            
            top_strategies = df.head(top_n)
            
            for i, row in top_strategies.iterrows():
                rank = top_strategies.index.get_loc(i) + 1
                f.write(f"#{rank:2d}. {row['strategy']}\n")
                f.write(f"     Total Return: {row['total_profit_percent']:8.2f}%\n")
                f.write(f"     Total Trades: {row['total_trades']:8.0f}\n")
                f.write(f"     Win Rate:     {row['win_rate']:8.1f}%\n")
                f.write(f"     Max Drawdown: {row['max_drawdown']:8.2f}%\n")
                f.write(f"     Avg Duration: {row['avg_duration']}\n")
                if row['best_pair']:
                    f.write(f"     Best Pair:    {row['best_pair']}\n")
                if 'sharpe_ratio' in row and row['sharpe_ratio']:
                    f.write(f"     Sharpe Ratio: {row['sharpe_ratio']:8.2f}\n")
                if 'profit_factor' in row and row['profit_factor']:
                    f.write(f"     Profit Factor:{row['profit_factor']:8.2f}\n")
                f.write("\n")
        
        logger.info(f"🏆 Top performers report saved: {top_file}")
    
    def display_top_performers_summary(self, df: pd.DataFrame, top_n: int):
        """Display a summary of top performers in the console."""
        print(f"\n🏆 TOP {top_n} PERFORMING STRATEGIES")
        print("=" * 80)
        
        top_strategies = df.head(top_n)
        
        # Display table header
        print(f"{'Rank':<4} {'Strategy':<25} {'Return':<8} {'Trades':<7} {'Win Rate':<8} {'Max DD':<8} {'Sharpe':<7}")
        print("-" * 80)
        
        for i, row in top_strategies.iterrows():
            rank = top_strategies.index.get_loc(i) + 1
            strategy_name = row['strategy'][:24]  # Truncate long names
            sharpe_str = f"{row['sharpe_ratio']:6.2f}" if row.get('sharpe_ratio') else "  N/A"
            print(f"{rank:<4} {strategy_name:<25} {row['total_profit_percent']:>6.2f}% {row['total_trades']:>6.0f} {row['win_rate']:>6.1f}% {row['max_drawdown']:>6.2f}% {sharpe_str}")
        
        print("\n📊 SUMMARY STATISTICS")
        print("-" * 30)
        profitable = df[df['total_profit_percent'] > 0]
        print(f"Total strategies analyzed: {len(df)}")
        print(f"Profitable strategies: {len(profitable)} ({(len(profitable)/len(df))*100:.1f}%)")
        print(f"Average return: {df['total_profit_percent'].mean():.2f}%")
        print(f"Best performer: {df.iloc[0]['strategy']} ({df.iloc[0]['total_profit_percent']:.2f}%)")
        print(f"Worst performer: {df.iloc[-1]['strategy']} ({df.iloc[-1]['total_profit_percent']:.2f}%)")
        
        if self.failed_strategies:
            print(f"\n❌ Failed strategies: {len(self.failed_strategies)}")
    
    def list_strategies_by_criteria(self, min_return: float = None, min_trades: int = None, 
                                   max_drawdown: float = None, min_win_rate: float = None,
                                   min_sharpe: float = None, min_profit_factor: float = None):
        """List strategies that meet specific criteria."""
        if not self.results:
            logger.error("❌ No results found to filter!")
            return
        
        df = pd.DataFrame(list(self.results.values()))
        filtered_df = df.copy()
        
        criteria = []
        if min_return is not None:
            filtered_df = filtered_df[filtered_df['total_profit_percent'] >= min_return]
            criteria.append(f"return >= {min_return}%")
        
        if min_trades is not None:
            filtered_df = filtered_df[filtered_df['total_trades'] >= min_trades]
            criteria.append(f"trades >= {min_trades}")
        
        if max_drawdown is not None:
            filtered_df = filtered_df[filtered_df['max_drawdown'] <= max_drawdown]
            criteria.append(f"max_drawdown <= {max_drawdown}%")
        
        if min_win_rate is not None:
            filtered_df = filtered_df[filtered_df['win_rate'] >= min_win_rate]
            criteria.append(f"win_rate >= {min_win_rate}%")
        
        if min_sharpe is not None and 'sharpe_ratio' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['sharpe_ratio'] >= min_sharpe]
            criteria.append(f"sharpe >= {min_sharpe}")
        
        if min_profit_factor is not None and 'profit_factor' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['profit_factor'] >= min_profit_factor]
            criteria.append(f"profit_factor >= {min_profit_factor}")
        
        # Sort by return
        filtered_df = filtered_df.sort_values('total_profit_percent', ascending=False)
        
        print(f"\n🔍 STRATEGIES MATCHING CRITERIA: {', '.join(criteria)}")
        print("=" * 80)
        
        if len(filtered_df) == 0:
            print("❌ No strategies match the specified criteria.")
            return
        
        print(f"Found {len(filtered_df)} strategies:")
        print(f"{'Strategy':<25} {'Return':<8} {'Trades':<7} {'Win Rate':<8} {'Max DD':<8} {'Sharpe':<7}")
        print("-" * 80)
        
        for _, row in filtered_df.iterrows():
            strategy_name = row['strategy'][:24]
            sharpe_str = f"{row['sharpe_ratio']:6.2f}" if row.get('sharpe_ratio') else "  N/A"
            print(f"{strategy_name:<25} {row['total_profit_percent']:>6.2f}% {row['total_trades']:>6.0f} {row['win_rate']:>6.1f}% {row['max_drawdown']:>6.2f}% {sharpe_str}")

def main():
    parser = argparse.ArgumentParser(description='Strategy Comparison Tool - Analyze backtest results')
    parser.add_argument('--num-strategies', '-n', type=int, default=20, 
                       help='Number of top strategies to show (default: 20)')
    parser.add_argument('--results-dir', default='user_data/backtest_results',
                       help='Directory containing backtest results')
    parser.add_argument('--min-return', type=float, help='Minimum return percentage filter')
    parser.add_argument('--min-trades', type=int, help='Minimum number of trades filter')
    parser.add_argument('--max-drawdown', type=float, help='Maximum drawdown percentage filter')
    parser.add_argument('--min-win-rate', type=float, help='Minimum win rate percentage filter')
    parser.add_argument('--min-sharpe', type=float, help='Minimum Sharpe ratio filter')
    parser.add_argument('--min-profit-factor', type=float, help='Minimum profit factor filter')
    parser.add_argument('--filter-only', action='store_true', 
                       help='Only show filtered results, skip generating reports')
    
    args = parser.parse_args()
    
    print("🔍 Strategy Comparison Tool")
    print("=" * 40)
    
    comparison = StrategyComparison(args.results_dir)
    
    try:
        # Collect all results
        comparison.collect_all_results()
        
        if not comparison.results:
            logger.error("❌ No backtest results found!")
            logger.info("💡 Make sure you have run backtests first using strategy_backtester.py")
            return
        
        # Apply filters if specified
        if any([args.min_return, args.min_trades, args.max_drawdown, args.min_win_rate, args.min_sharpe, args.min_profit_factor]):
            comparison.list_strategies_by_criteria(
                min_return=args.min_return,
                min_trades=args.min_trades,
                max_drawdown=args.max_drawdown,
                min_win_rate=args.min_win_rate,
                min_sharpe=args.min_sharpe,
                min_profit_factor=args.min_profit_factor
            )
            
            if args.filter_only:
                return
        
        # Generate comparison reports
        comparison.generate_comparison_report(args.num_strategies)
        
    except Exception as e:
        logger.error(f"💥 Error: {e}")
        return

if __name__ == "__main__":
    main() 