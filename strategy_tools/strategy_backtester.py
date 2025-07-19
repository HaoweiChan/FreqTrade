#!/usr/bin/env python3
"""
Freqtrade Strategy Backtesting and Comparison Tool
This script automatically backtests all strategies and compares their performance.
"""

import re
import json
import time
import psutil
import logging
import argparse
import subprocess
import concurrent.futures
import multiprocessing
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy_backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StrategyBacktester:
    def __init__(self, config_path: str = "user_data/config.json", max_workers: int = None):
        self.config_path = config_path
        self.results_dir = Path("user_data/backtest_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Backtest parameters
        self.start_date = "20240101"
        self.end_date = "20241231"
        self.timeframe = "5m"
        
        # Parallel processing settings
        self.max_workers = max_workers or min(multiprocessing.cpu_count(), 6)
        
        # Timeout settings
        self.strategy_timeout = 300  # 5 minutes per strategy
        self.discovery_timeout = 60  # 1 minute for strategy discovery
        
        # Results storage
        self.results = {}
        self.failed_strategies = []
        
        # Individual strategy results directory
        self.individual_results_dir = self.results_dir / "individual_results"
        self.individual_results_dir.mkdir(exist_ok=True)
        
        # Timeframe cache for strategy analysis
        self.timeframe_cache = {}
        
        logger.info(f"Initialized backtester with {self.max_workers} workers")

    def detect_strategy_timeframe(self, strategy_name: str) -> str:
        """Detect optimal timeframe for strategy by analyzing the strategy file."""
        if strategy_name in self.timeframe_cache:
            return self.timeframe_cache[strategy_name]
        
        strategy_file = Path(f"user_data/strategies/{strategy_name}/{strategy_name}.py")
        if not strategy_file.exists():
            self.timeframe_cache[strategy_name] = "5m"
            return "5m"
        
        try:
            with open(strategy_file, 'r') as f:
                content = f.read()
            
            # Look for timeframe definitions
            timeframe_patterns = [
                r'timeframe\s*=\s*["\']([^"\']+)["\']',
                r'TIMEFRAME\s*=\s*["\']([^"\']+)["\']',
                r'informative_timeframe\s*=\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in timeframe_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    detected_timeframe = matches[0]
                    self.timeframe_cache[strategy_name] = detected_timeframe
                    logger.debug(f"Detected timeframe {detected_timeframe} for strategy {strategy_name}")
                    return detected_timeframe
            
            # Fallback to 5m if no timeframe detected
            self.timeframe_cache[strategy_name] = "5m"
            return "5m"
            
        except Exception as e:
            logger.warning(f"Error detecting timeframe for {strategy_name}: {e}")
            self.timeframe_cache[strategy_name] = "5m"
            return "5m"

    def get_compatible_strategies(self) -> List[str]:
        """Get list of strategies that are compatible with current freqtrade version."""
        logger.info("Checking strategy compatibility...")
        
        compatible_strategies = []
        strategies_dir = Path("user_data/strategies")
        
        try:
            # Find all Python files with populate_entry_trend
            result = subprocess.run(
                ["grep", "-r", "populate_entry_trend", str(strategies_dir)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Extract strategy names from file paths
                for line in result.stdout.split('\n'):
                    if line.strip() and '.py:' in line:
                        file_path = line.split(':')[0]
                        if file_path.endswith('.py'):
                            # Extract strategy name from path
                            strategy_path = Path(file_path)
                            strategy_name = strategy_path.parent.name
                            if strategy_name not in compatible_strategies:
                                compatible_strategies.append(strategy_name)
            
            logger.info(f"Found {len(compatible_strategies)} compatible strategies")
            return sorted(compatible_strategies)
            
        except Exception as e:
            logger.error(f"Error checking compatibility: {e}")
            return []
    
    def discover_strategies_from_filesystem(self) -> List[str]:
        """Discover strategies by scanning the filesystem."""
        logger.info("Discovering strategies from filesystem...")
        
        strategies = []
        strategies_dir = Path("user_data/strategies")
        
        if not strategies_dir.exists():
            logger.error(f"Strategies directory not found: {strategies_dir}")
            return []
        
        # Find all strategy directories
        for strategy_dir in strategies_dir.iterdir():
            if strategy_dir.is_dir() and not strategy_dir.name.startswith('.'):
                # Check if there's a Python file with the same name
                strategy_file = strategy_dir / f"{strategy_dir.name}.py"
                if strategy_file.exists():
                    strategies.append(strategy_dir.name)
        
        logger.info(f"Found {len(strategies)} strategies from filesystem")
        return sorted(strategies)
    
    def discover_strategies(self, compatible_only: bool = False) -> List[str]:
        """Discover all strategies using freqtrade's native discovery."""
        
        if compatible_only:
            logger.info("Discovering compatible strategies only...")
            return self.get_compatible_strategies()
        
        logger.info("Discovering strategies using freqtrade...")
        
        try:
            # Use freqtrade's native strategy discovery with timeout
            result = subprocess.run(
                ["freqtrade", "list-strategies", "--one-column", "--config", self.config_path],
                capture_output=True,
                text=True,
                timeout=self.discovery_timeout
            )
            
            if result.returncode == 0:
                strategies = []
                for line in result.stdout.strip().split('\n'):
                    strategy = line.strip()
                    if strategy and not strategy.startswith('2025-'):  # Filter out log lines
                        strategies.append(strategy)
                
                logger.info(f"Found {len(strategies)} strategies via freqtrade discovery")
                return sorted(strategies)
            else:
                logger.error(f"Failed to discover strategies via freqtrade: {result.stderr}")
                logger.info("Falling back to filesystem discovery...")
                return self.discover_strategies_from_filesystem()
                
        except subprocess.TimeoutExpired:
            logger.error("Freqtrade discovery timed out, falling back to filesystem discovery...")
            return self.discover_strategies_from_filesystem()
        except Exception as e:
            logger.error(f"Error discovering strategies via freqtrade: {e}")
            logger.info("Falling back to filesystem discovery...")
            return self.discover_strategies_from_filesystem()
    
    def get_strategy_result_file(self, strategy_name: str) -> Path:
        """Get the file path for a strategy's result."""
        return self.individual_results_dir / f"{strategy_name}_result.json"
    
    def load_existing_result(self, strategy_name: str) -> Optional[Dict]:
        """Load existing backtest result if it exists."""
        result_file = self.get_strategy_result_file(strategy_name)
        if result_file.exists():
            try:
                with open(result_file, 'r') as f:
                    result = json.load(f)
                    # Verify the result is for the same time period
                    if (result.get('backtest_config', {}).get('start_date') == self.start_date and
                        result.get('backtest_config', {}).get('end_date') == self.end_date):
                        logger.info(f"✅ Found existing result for {strategy_name}")
                        return result
                    else:
                        logger.info(f"🔄 Existing result for {strategy_name} uses different parameters, will re-run")
                        return None
            except Exception as e:
                logger.warning(f"⚠️ Could not load existing result for {strategy_name}: {e}")
                return None
        return None
    
    def save_strategy_result(self, strategy_name: str, result: Dict):
        """Save strategy result to file."""
        result_file = self.get_strategy_result_file(strategy_name)
        try:
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"💾 Saved result for {strategy_name}")
        except Exception as e:
            logger.error(f"❌ Failed to save result for {strategy_name}: {e}")
    
    def run_backtest_worker(self, strategy_name: str) -> Optional[Dict]:
        """Worker function for parallel processing of a single strategy."""
        try:
            # Check if we already have a result for this strategy
            existing_result = self.load_existing_result(strategy_name)
            if existing_result:
                return existing_result
            
            logger.info(f"🔄 Worker processing strategy: {strategy_name}")
            
            # Create individual results directory for this strategy
            strategy_results_dir = self.results_dir / strategy_name
            strategy_results_dir.mkdir(exist_ok=True)
            
            # Detect optimal timeframe for this strategy
            detected_timeframe = self.detect_strategy_timeframe(strategy_name)
            
            # Construct freqtrade backtest command
            cmd = [
                "freqtrade", "backtesting",
                "--config", self.config_path,
                "--strategy", strategy_name,
                "--timerange", f"{self.start_date}-{self.end_date}",
                "--timeframe", detected_timeframe,
                "--export", "trades",
                "--export-filename", str(strategy_results_dir / f"{strategy_name}_backtest.json")
            ]
            
            # Run the backtest with timeout
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.strategy_timeout
            )
            end_time = time.time()
            
            if result.returncode == 0:
                # Parse the output to extract key metrics
                metrics = self.parse_backtest_output(result.stdout, strategy_name)
                
                # Add metadata
                metadata = {
                    'execution_time': end_time - start_time,
                    'backtest_timestamp': datetime.now().isoformat(),
                    'detected_timeframe': detected_timeframe,
                    'backtest_config': {
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'config_path': self.config_path,
                        'timeframe': detected_timeframe
                    },
                    'freqtrade_version': self.get_freqtrade_version(),
                    'command_executed': ' '.join(cmd)
                }
                
                # Combine metrics and metadata
                full_result = {**metrics, **metadata}
                
                # Save detailed output
                with open(strategy_results_dir / f"{strategy_name}_output.txt", 'w') as f:
                    f.write(result.stdout)
                
                # Save the result to file
                self.save_strategy_result(strategy_name, full_result)
                
                logger.info(f"✅ {strategy_name} completed successfully in {end_time - start_time:.1f}s (timeframe: {detected_timeframe})")
                return full_result
            else:
                logger.error(f"❌ {strategy_name} failed: {result.stderr}")
                failed_result = {
                    'strategy': strategy_name,
                    'error': result.stderr,
                    'stdout': result.stdout,
                    'detected_timeframe': detected_timeframe,
                    'failed_timestamp': datetime.now().isoformat(),
                    'backtest_config': {
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'config_path': self.config_path,
                        'timeframe': detected_timeframe
                    }
                }
                
                # Save failed result to file
                failed_file = self.individual_results_dir / f"{strategy_name}_failed.json"
                try:
                    with open(failed_file, 'w') as f:
                        json.dump(failed_result, f, indent=2)
                except Exception as e:
                    logger.error(f"Could not save failed result: {e}")
                
                # Clean up empty strategy directory
                self.cleanup_failed_strategy_directory(strategy_results_dir, strategy_name)
                
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {strategy_name} timed out after {self.strategy_timeout} seconds")
            failed_result = {
                'strategy': strategy_name,
                'error': f'Timeout after {self.strategy_timeout} seconds',
                'stdout': '',
                'failed_timestamp': datetime.now().isoformat(),
                'backtest_config': {
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                    'config_path': self.config_path
                }
            }
            
            # Save failed result to file
            failed_file = self.individual_results_dir / f"{strategy_name}_failed.json"
            try:
                with open(failed_file, 'w') as f:
                    json.dump(failed_result, f, indent=2)
            except Exception as e:
                logger.error(f"Could not save failed result: {e}")
            
            # Clean up empty strategy directory
            strategy_results_dir = self.results_dir / strategy_name
            self.cleanup_failed_strategy_directory(strategy_results_dir, strategy_name)
            
            return None
        except Exception as e:
            logger.error(f"💥 {strategy_name} error: {str(e)}")
            failed_result = {
                'strategy': strategy_name,
                'error': str(e),
                'stdout': '',
                'failed_timestamp': datetime.now().isoformat(),
                'backtest_config': {
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                    'config_path': self.config_path
                }
            }
            
            # Save failed result to file
            failed_file = self.individual_results_dir / f"{strategy_name}_failed.json"
            try:
                with open(failed_file, 'w') as f:
                    json.dump(failed_result, f, indent=2)
            except Exception as e:
                logger.error(f"Could not save failed result: {e}")
            
            # Clean up empty strategy directory
            strategy_results_dir = self.results_dir / strategy_name
            self.cleanup_failed_strategy_directory(strategy_results_dir, strategy_name)
            
            return None

    def run_parallel_backtests(self, strategies: List[str]) -> Dict:
        """Run backtests for strategies in parallel."""
        logger.info(f"🚀 Starting parallel backtesting of {len(strategies)} strategies with {self.max_workers} workers")
        
        # Track results and progress
        completed_results = {}
        failed_results = []
        start_time = time.time()
        
        # Monitor system resources
        initial_memory = psutil.virtual_memory().percent
        initial_cpu = psutil.cpu_percent()
        logger.info(f"Initial system state - Memory: {initial_memory:.1f}%, CPU: {initial_cpu:.1f}%")
        
        # Use ProcessPoolExecutor for parallel execution
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all strategies for processing
            future_to_strategy = {
                executor.submit(self.run_backtest_worker, strategy): strategy 
                for strategy in strategies
            }
            
            # Track progress
            total_strategies = len(strategies)
            success_count = 0
            failed_count = 0
            
            # Process completed futures
            for future in concurrent.futures.as_completed(future_to_strategy):
                strategy_name = future_to_strategy[future]
                try:
                    result = future.result()
                    if result:
                        completed_results[strategy_name] = result
                        success_count += 1
                        
                        # Calculate progress and ETA
                        completed_count = success_count + failed_count
                        elapsed_time = time.time() - start_time
                        progress_pct = completed_count / total_strategies * 100
                        
                        if completed_count > 0:
                            avg_time_per_strategy = elapsed_time / completed_count
                            remaining_strategies = total_strategies - completed_count
                            eta_seconds = remaining_strategies * avg_time_per_strategy
                            eta_minutes = eta_seconds / 60
                            
                            logger.info(f"✅ Completed {strategy_name} | Progress: {completed_count}/{total_strategies} ({progress_pct:.1f}%) | Success: {success_count} | ETA: {eta_minutes:.1f}m")
                        else:
                            logger.info(f"✅ Completed {strategy_name} | Progress: {completed_count}/{total_strategies} ({progress_pct:.1f}%) | Success: {success_count}")
                    else:
                        failed_results.append({'strategy': strategy_name, 'error': 'No result returned'})
                        failed_count += 1
                        
                        completed_count = success_count + failed_count
                        progress_pct = completed_count / total_strategies * 100
                        logger.error(f"❌ Failed {strategy_name} | Progress: {completed_count}/{total_strategies} ({progress_pct:.1f}%) | Success: {success_count} | Failed: {failed_count}")
                        
                    # Monitor system resources periodically
                    if completed_count % 5 == 0:  # Every 5 completed strategies
                        current_memory = psutil.virtual_memory().percent
                        current_cpu = psutil.cpu_percent()
                        
                        if current_memory > initial_memory + 20:  # If memory increased by 20%
                            logger.warning(f"⚠️ High memory usage: {current_memory:.1f}% (was {initial_memory:.1f}%)")
                        
                        logger.info(f"📊 System status - Memory: {current_memory:.1f}%, CPU: {current_cpu:.1f}%")
                        
                except Exception as e:
                    logger.error(f"💥 Exception processing {strategy_name}: {e}")
                    failed_results.append({'strategy': strategy_name, 'error': str(e)})
                    failed_count += 1
                    
                    completed_count = success_count + failed_count
                    progress_pct = completed_count / total_strategies * 100
                    logger.error(f"💥 Exception {strategy_name} | Progress: {completed_count}/{total_strategies} ({progress_pct:.1f}%) | Success: {success_count} | Failed: {failed_count}")
        
        # Update instance variables
        self.results = completed_results
        self.failed_strategies = failed_results
        
        # Final summary
        total_time = time.time() - start_time
        avg_time_per_strategy = total_time / len(strategies) if len(strategies) > 0 else 0
        
        logger.info(f"🏁 Parallel backtesting completed in {total_time:.1f}s")
        logger.info(f"📈 Results: {len(completed_results)} successful, {len(failed_results)} failed")
        logger.info(f"⚡ Average time per strategy: {avg_time_per_strategy:.1f}s")
        
        if len(completed_results) > 0:
            total_execution_time = sum(result.get('execution_time', 0) for result in completed_results.values())
            efficiency = total_execution_time / total_time if total_time > 0 else 0
            logger.info(f"🚀 Parallel efficiency: {efficiency:.1f}x (total work: {total_execution_time:.1f}s)")
        
        return completed_results

    def parse_backtest_output(self, output: str, strategy_name: str) -> Dict:
        """Parse freqtrade backtest output to extract key metrics."""
        metrics = {
            'strategy': strategy_name,
            'total_return': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'avg_profit': 0.0,
            'total_profit_abs': 0.0,
            'total_profit_percent': 0.0,
            'avg_duration': '',
            'best_pair': '',
            'worst_pair': '',
            'backtest_start': '',
            'backtest_end': '',
            'market_change': 0.0
        }
        
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Parse the new freqtrade output format with box-drawing characters
            if '│' in line:
                parts = [part.strip() for part in line.split('│')]
                
                # Total profit percentage (parts[0] is empty, data in parts[1] and parts[2])
                if len(parts) >= 4 and 'Total profit %' in parts[1]:
                    try:
                        profit_str = parts[2]
                        if '%' in profit_str:
                            metrics['total_profit_percent'] = float(profit_str.replace('%', ''))
                    except:
                        pass
                
                # Absolute profit
                elif len(parts) >= 4 and 'Absolute profit' in parts[1]:
                    try:
                        profit_str = parts[2]
                        if 'USDT' in profit_str:
                            metrics['total_profit_abs'] = float(profit_str.replace('USDT', '').strip())
                    except:
                        pass
                
                # Sharpe ratio
                elif len(parts) >= 4 and 'Sharpe' in parts[1]:
                    try:
                        metrics['sharpe_ratio'] = float(parts[2])
                    except:
                        pass
                
                # Profit factor
                elif len(parts) >= 4 and 'Profit factor' in parts[1]:
                    try:
                        metrics['profit_factor'] = float(parts[2])
                    except:
                        pass
                
                # Best Pair
                elif len(parts) >= 4 and 'Best Pair' in parts[1]:
                    metrics['best_pair'] = parts[2]
                
                # Worst Pair
                elif len(parts) >= 4 and 'Worst Pair' in parts[1]:
                    metrics['worst_pair'] = parts[2]
                
                # Max drawdown percentage
                elif len(parts) >= 4 and ('Max % of account underwater' in parts[1] or 'Absolute Drawdown (Account)' in parts[1]):
                    try:
                        dd_str = parts[2]
                        if '%' in dd_str:
                            metrics['max_drawdown'] = float(dd_str.replace('%', ''))
                    except:
                        pass
                
                # Market change
                elif len(parts) >= 4 and 'Market change' in parts[1]:
                    try:
                        market_str = parts[2]
                        if '%' in market_str:
                            metrics['market_change'] = float(market_str.replace('%', ''))
                    except:
                        pass
            
            # Parse strategy summary table (the final table with strategy name)
            if strategy_name in line and '│' in line:
                parts = [part.strip() for part in line.split('│')]
                if len(parts) >= 9:
                    try:
                        # Strategy table format: '' | Strategy | Trades | Avg Profit % | Tot Profit USDT | Tot Profit % | Avg Duration | Win Draw Loss Win% | Drawdown | ''
                        # Note: parts[0] and parts[-1] are empty strings
                        metrics['total_trades'] = int(parts[2])
                        metrics['avg_profit'] = float(parts[3])
                        
                        # Parse total profit USDT
                        metrics['total_profit_abs'] = float(parts[4])
                        
                        # Parse total profit %
                        metrics['total_profit_percent'] = float(parts[5])
                        
                        # Parse duration
                        metrics['avg_duration'] = parts[6]
                        
                        # Parse win/draw/loss stats
                        win_stats = parts[7].strip()
                        if win_stats:
                            # Format: "352  2  303  53.6"
                            stats_parts = win_stats.split()
                            if len(stats_parts) >= 4:
                                metrics['winning_trades'] = int(stats_parts[0])
                                # Draw trades at index 1
                                metrics['losing_trades'] = int(stats_parts[2])
                                metrics['win_rate'] = float(stats_parts[3])
                        
                    except Exception as e:
                        logger.debug(f"Error parsing strategy summary line: {e}")
                        pass
            
            # Parse backtest date range
            if 'Backtested' in line and '->' in line:
                try:
                    # Format: "Backtested 2024-01-01 00:00:00 -> 2024-03-31 00:00:00"
                    date_part = line.split('Backtested')[1].split('|')[0].strip()
                    if '->' in date_part:
                        start_date, end_date = date_part.split('->')
                        metrics['backtest_start'] = start_date.strip()
                        metrics['backtest_end'] = end_date.strip()
                except:
                    pass
        
        return metrics
    
    def get_freqtrade_version(self) -> str:
        """Get freqtrade version."""
        try:
            result = subprocess.run(['freqtrade', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "unknown"
        except:
            return "unknown"
    
    def cleanup_failed_strategy_directory(self, strategy_dir: Path, strategy_name: str):
        """Clean up strategy directory when backtest fails."""
        try:
            if strategy_dir.exists():
                # Check if directory is empty or contains only partial/failed files
                files_in_dir = list(strategy_dir.iterdir())
                
                # Remove the directory if it's empty or contains only partial files
                if not files_in_dir:
                    # Directory is empty, remove it
                    strategy_dir.rmdir()
                    logger.info(f"🧹 Removed empty directory for failed strategy: {strategy_name}")
                else:
                    # Check if it only contains partial files (no complete backtest results)
                    has_complete_results = any(
                        f.suffix == '.json' and 'backtest' in f.name and f.stat().st_size > 1000
                        for f in files_in_dir if f.is_file()
                    )
                    
                    if not has_complete_results:
                        # Only partial files, clean up the directory
                        import shutil
                        shutil.rmtree(strategy_dir)
                        logger.info(f"🧹 Removed directory with partial files for failed strategy: {strategy_name}")
                    else:
                        logger.debug(f"Keeping directory for {strategy_name} - contains complete results")
        except Exception as e:
            logger.warning(f"Could not clean up directory for {strategy_name}: {e}")
    
    def cleanup_empty_directories(self):
        """Clean up any existing empty directories in backtest results."""
        if not self.results_dir.exists():
            return
        
        try:
            empty_dirs = []
            for item in self.results_dir.iterdir():
                if item.is_dir() and item.name not in ['individual_results']:
                    # Check if directory is empty
                    try:
                        if not any(item.iterdir()):
                            empty_dirs.append(item)
                    except:
                        pass  # Skip if we can't read the directory
            
            if empty_dirs:
                logger.info(f"🧹 Cleaning up {len(empty_dirs)} empty directories...")
                for empty_dir in empty_dirs:
                    try:
                        empty_dir.rmdir()
                        logger.debug(f"Removed empty directory: {empty_dir.name}")
                    except Exception as e:
                        logger.warning(f"Could not remove empty directory {empty_dir.name}: {e}")
                logger.info(f"✅ Cleaned up {len(empty_dirs)} empty directories")
            else:
                logger.debug("No empty directories found to clean up")
                
        except Exception as e:
            logger.warning(f"Error during directory cleanup: {e}")
    
    def collect_all_results(self):
        """Collect all existing results from files."""
        # Import here to avoid circular imports
        import sys
        import os
        
        # Add current directory to path so we can import utils
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        try:
            import utils
            # Use shared utilities for comprehensive result detection
            utils_instance = utils.StrategyResultsUtils(str(self.results_dir))
            self.results, self.failed_strategies = utils_instance.collect_all_results()
            logger.info(f"Loaded {len(self.results)} successful and {len(self.failed_strategies)} failed results using shared utils")
        except Exception as e:
            logger.warning(f"Failed to use shared utils for result collection, falling back: {e}")
            # Fallback to the old method
            self.results = {}
            self.failed_strategies = []
            
            if not self.individual_results_dir.exists():
                return
            
            # Load successful results
            for result_file in self.individual_results_dir.glob("*_result.json"):
                try:
                    with open(result_file, 'r') as f:
                        result = json.load(f)
                        strategy_name = result.get('strategy', result_file.stem.replace('_result', ''))
                        self.results[strategy_name] = result
                        logger.debug(f"Loaded existing result for {strategy_name}")
                except Exception as e:
                    logger.warning(f"Could not load result from {result_file}: {e}")
            
            # Load failed results
            for failed_file in self.individual_results_dir.glob("*_failed.json"):
                try:
                    with open(failed_file, 'r') as f:
                        failed_result = json.load(f)
                        self.failed_strategies.append(failed_result)
                        logger.debug(f"Loaded failed result for {failed_result.get('strategy', 'unknown')}")
                except Exception as e:
                    logger.warning(f"Could not load failed result from {failed_file}: {e}")
            
            logger.info(f"Loaded {len(self.results)} successful and {len(self.failed_strategies)} failed results from previous runs")
    
    def get_previously_successful_strategies(self) -> List[str]:
        """Get list of strategies that were previously successful."""
        # Import here to avoid circular imports
        import sys
        import os
        
        # Add current directory to path so we can import utils
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        try:
            import utils
            successful_strategies = utils.discover_successful_strategies(str(self.results_dir))
            logger.info(f"Found {len(successful_strategies)} previously successful strategies using shared utils")
            return successful_strategies
        except Exception as e:
            logger.warning(f"Failed to use shared utils, falling back to simple detection: {e}")
            # Fallback to the old simple method
            successful_strategies = []
            
            if not self.individual_results_dir.exists():
                logger.warning("No individual results directory found. Run some backtests first.")
                return []
            
            # Find all successful result files
            for result_file in self.individual_results_dir.glob("*_result.json"):
                try:
                    strategy_name = result_file.stem.replace('_result', '')
                    successful_strategies.append(strategy_name)
                    logger.debug(f"Found successful strategy: {strategy_name}")
                except Exception as e:
                    logger.warning(f"Could not parse result file {result_file}: {e}")
            
            logger.info(f"Found {len(successful_strategies)} previously successful strategies")
            return sorted(successful_strategies)
    
    def get_strategies_to_process(self, all_strategies: List[str], include_failed: bool = True) -> List[str]:
        """Get list of strategies that need to be processed (pending or optionally failed)."""
        already_completed = set(self.results.keys())
        already_failed = {fs.get('strategy') for fs in self.failed_strategies}
        
        # Start with pending strategies
        pending_strategies = [s for s in all_strategies if s not in already_completed and s not in already_failed]
        
        strategies_to_run = pending_strategies.copy()
        
        # Optionally include failed strategies for retry
        if include_failed:
            failed_strategies = [s for s in all_strategies if s in already_failed]
            strategies_to_run.extend(failed_strategies)
        
        logger.info(f"Strategies to process: {len(pending_strategies)} pending" + 
                   (f", {len(failed_strategies)} failed (retry)" if include_failed and failed_strategies else ""))
        
        return strategies_to_run
    
    def run_all_backtests(self, strategies: List[str] = None, max_strategies: int = None, include_failed_retry: bool = False, compatible_only: bool = False, successful_only: bool = False):
        """Run backtests for all discovered strategies."""
        # Load any existing results
        self.collect_all_results()
        
        if strategies is None:
            if successful_only:
                # Only use previously successful strategies
                all_strategies = self.get_previously_successful_strategies()
                if not all_strategies:
                    logger.error("No previously successful strategies found! Run some backtests first or remove --successful-only flag.")
                    return
                logger.info(f"🎯 Focusing on {len(all_strategies)} previously successful strategies")
                # For successful-only mode, we want to re-run all of them
                strategies = all_strategies
            else:
                # Auto-discover all strategies
                all_strategies = self.discover_strategies(compatible_only=compatible_only)
                if not all_strategies:
                    logger.error("No strategies discovered! Check your strategy directory.")
                    return
                
                # Get strategies that need processing
                strategies = self.get_strategies_to_process(all_strategies, include_failed=include_failed_retry)
                
                if not strategies:
                    logger.info("🎉 All strategies have been successfully processed!")
                    logger.info(f"Completed: {len(self.results)}, Failed: {len(self.failed_strategies)}")
                    return
        
        if max_strategies:
            strategies = strategies[:max_strategies]
            logger.info(f"Limited to first {max_strategies} strategies")
        
        total_strategies = len(strategies)
        logger.info(f"Starting batch processing of {total_strategies} strategies...")
        
        # Use parallel processing (workers=1 provides sequential behavior)
        if len(strategies) > 1 and self.max_workers > 1:
            # Use parallel processing with multiple workers
            start_time = time.time()
            results = self.run_parallel_backtests(strategies)
            end_time = time.time()
            
            logger.info(f"🚀 Parallel processing completed in {end_time - start_time:.1f}s")
            logger.info(f"Average time per strategy: {(end_time - start_time) / len(strategies):.1f}s")
            
        else:
            # Use sequential processing (single worker or single strategy)
            if self.max_workers == 1:
                logger.info("Using sequential processing (1 worker)...")
            else:
                logger.info("Using sequential processing (single strategy)...")
                
            for i, strategy in enumerate(strategies, 1):
                logger.info(f"📊 Progress: {i}/{total_strategies} ({(i/total_strategies)*100:.1f}%) - Processing {strategy}")
                
                result = self.run_backtest_worker(strategy)
                if result:
                    self.results[strategy] = result
                    logger.info(f"✅ Successfully completed {strategy}")
                else:
                    logger.info(f"❌ Failed to complete {strategy}")
        
        # Final summary
        self.collect_all_results()  # Reload to get latest counts
        logger.info(f"🏁 Batch completed! Total successful: {len(self.results)}, Total failed: {len(self.failed_strategies)}")
        
        # Check if there are more strategies to process
        if strategies is None or len(strategies) >= max_strategies if max_strategies else True:
            remaining_strategies = self.get_strategies_to_process(self.discover_strategies(), include_failed=False)
            if remaining_strategies:
                logger.info(f"📋 {len(remaining_strategies)} strategies still pending for future runs")
            else:
                logger.info("🎉 All strategies have been processed!")
        
        # Clean up any empty directories from failed backtests
        logger.info("🧹 Cleaning up empty directories...")
        self.cleanup_empty_directories()
                
        # Report generation is handled separately by strategy_comparison.py
    
    def save_intermediate_results(self):
        """Save intermediate results to prevent data loss."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save successful results
        if self.results:
            results_file = self.results_dir / f"intermediate_results_{timestamp}.json"
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
        
        # Save failed strategies
        if self.failed_strategies:
            failed_file = self.results_dir / f"failed_strategies_{timestamp}.json"
            with open(failed_file, 'w') as f:
                json.dump(self.failed_strategies, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Freqtrade Strategy Backtesting Tool')
    parser.add_argument('--config', default='user_data/config.json', help='Config file path')
    parser.add_argument('--max-strategies', type=int, help='Limit number of strategies to test per batch')
    parser.add_argument('--strategy', help='Test specific strategy only')
    parser.add_argument('--retry-failed', action='store_true', help='Include failed strategies for retry')
    parser.add_argument('--continuous', action='store_true', help='Run continuously until all strategies are processed')
    parser.add_argument('--compatible-only', action='store_true', help='Only test strategies compatible with current freqtrade version')
    parser.add_argument('--successful-only', action='store_true', help='Only test strategies that were previously successful')
    parser.add_argument('--workers', type=int, default=None, help='Number of workers for parallel processing (1 = sequential)')
    
    args = parser.parse_args()
    
    backtester = StrategyBacktester(args.config, args.workers)
    
    try:
        if args.strategy:
            # Test single strategy
            strategies = [args.strategy]
            backtester.run_all_backtests(strategies)
        else:
            # Auto-discover and process strategies
            if args.continuous:
                logger.info("🚀 Starting continuous backtesting mode...")
                logger.info("Will process all pending/failed strategies until completion")
                
                batch_count = 0
                while True:
                    batch_count += 1
                    logger.info(f"\n🔄 Starting batch #{batch_count}")
                    
                    # Load current state
                    backtester.collect_all_results()
                    all_strategies = backtester.discover_strategies(compatible_only=args.compatible_only)
                    
                    if not all_strategies:
                        logger.error("No strategies discovered!")
                        break
                    
                    # Get strategies to process
                    strategies_to_run = backtester.get_strategies_to_process(
                        all_strategies, 
                        include_failed=args.retry_failed
                    )
                    
                    if not strategies_to_run:
                        logger.info("🎉 All strategies completed! Continuous mode finished.")
                        break
                    
                    # Process batch
                    batch_size = args.max_strategies or len(strategies_to_run)
                    current_batch = strategies_to_run[:batch_size]
                    
                    backtester.run_all_backtests(
                        current_batch, 
                        max_strategies=batch_size,
                        include_failed_retry=args.retry_failed,
                        compatible_only=args.compatible_only,
                        successful_only=args.successful_only
                    )
                    
                    # Check if we should continue
                    if not args.max_strategies or len(strategies_to_run) <= batch_size:
                        logger.info("🏁 All remaining strategies processed!")
                        break
                    
                    logger.info(f"✅ Batch #{batch_count} completed. Continuing to next batch...")
            else:
                # Single batch run
                backtester.run_all_backtests(
                    strategies=None, 
                    max_strategies=args.max_strategies,
                    include_failed_retry=args.retry_failed,
                    compatible_only=args.compatible_only,
                    successful_only=args.successful_only
                )
        
        logger.info("✅ Backtesting completed successfully!")
        logger.info(f"📊 Results saved in: {backtester.results_dir}")
        logger.info(f"🔍 To analyze results, run: python strategy_tools/strategy_comparison.py")
        
    except KeyboardInterrupt:
        logger.info("⏹️  Backtesting interrupted by user")
        backtester.save_intermediate_results()
        logger.info(f"🔍 To analyze completed results, run: python strategy_tools/strategy_comparison.py")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        backtester.save_intermediate_results()

if __name__ == "__main__":
    main() 