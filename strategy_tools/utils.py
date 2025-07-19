#!/usr/bin/env python3
"""
Strategy Tools Utilities
Shared functions for strategy detection, result parsing, and common operations.
"""

import json
import zipfile
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class StrategyResultsUtils:
    """Utility class for working with strategy backtest results."""
    
    def __init__(self, results_dir: str = "user_data/backtest_results"):
        self.results_dir = Path(results_dir)
        self.individual_results_dir = self.results_dir / "individual_results"
    
    def parse_strategy_json_data(self, strategy_dir: Path) -> Optional[Dict]:
        """Parse structured JSON backtest data from a strategy directory."""
        try:
            # Check for .last_result.json to get the latest backtest
            last_result_file = strategy_dir / ".last_result.json"
            if not last_result_file.exists():
                logger.debug(f"No .last_result.json found in {strategy_dir}")
                return None
            
            # Load the latest result filename
            with open(last_result_file, 'r') as f:
                last_result = json.load(f)
            
            latest_backtest = last_result.get('latest_backtest')
            if not latest_backtest:
                logger.debug(f"No latest_backtest in {last_result_file}")
                return None
            
            # Handle both JSON files and ZIP files containing JSON
            json_filename = latest_backtest.replace('.zip', '.json')
            json_file = strategy_dir / json_filename
            zip_file = strategy_dir / latest_backtest
            
            backtest_data = None
            
            # Try to load JSON file first (if it exists)
            if json_file.exists():
                with open(json_file, 'r') as f:
                    backtest_data = json.load(f)
                    logger.debug(f"Loaded JSON file: {json_file}")
            
            # If no JSON file, try to extract from ZIP file
            elif zip_file.exists() and latest_backtest.endswith('.zip'):
                try:
                    with zipfile.ZipFile(zip_file, 'r') as zf:
                        # Look for the JSON file inside the ZIP
                        json_files = [name for name in zf.namelist() if name.endswith('.json') and not name.endswith('_config.json')]
                        if json_files:
                            # Use the first JSON file found (should be the backtest results)
                            json_filename_in_zip = json_files[0]
                            with zf.open(json_filename_in_zip) as json_in_zip:
                                backtest_data = json.load(json_in_zip)
                                logger.debug(f"Extracted JSON from ZIP: {zip_file} -> {json_filename_in_zip}")
                        else:
                            logger.debug(f"No JSON backtest file found in ZIP: {zip_file}")
                            return None
                except Exception as e:
                    logger.debug(f"Error extracting JSON from ZIP {zip_file}: {e}")
                    return None
            else:
                logger.debug(f"Neither JSON file nor ZIP file found for {strategy_dir.name}")
                return None
            
            if not backtest_data:
                logger.debug(f"No backtest data loaded for {strategy_dir.name}")
                return None
            
            # Extract strategy metrics from the structured data
            strategy_name = strategy_dir.name
            
            # Check if we have the expected structure
            if 'strategy' not in backtest_data:
                logger.warning(f"Invalid backtest structure in {strategy_dir}")
                return None
            
            # Get strategy data - the backtest_data should have strategy results
            strategy_data = backtest_data.get('strategy', {})
            if not strategy_data:
                logger.warning(f"No strategy data found in {strategy_dir}")
                return None
            
            # Extract key metrics from the comprehensive backtest data
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
                'market_change': 0.0,
                'cagr': 0.0,
                'expectancy': 0.0,
                'sortino': 0.0,
                'calmar': 0.0,
                'sqn': 0.0
            }
            
            # Extract metrics from the backtest data structure
            # Check for strategy_comparison section (newer format)
            strategy_comparison = backtest_data.get('strategy_comparison', [])
            if strategy_comparison and len(strategy_comparison) > 0:
                # Use the first (and usually only) strategy comparison entry
                comparison_data = strategy_comparison[0]
                
                metrics.update({
                    'total_trades': comparison_data.get('trades', 0),
                    'total_profit_percent': comparison_data.get('profit_total_pct', 0.0),
                    'total_profit_abs': comparison_data.get('profit_total_abs', 0.0),
                    'win_rate': comparison_data.get('winrate', 0.0) * 100,  # Convert to percentage
                    'profit_factor': comparison_data.get('profit_factor', 0.0),
                    'sharpe_ratio': comparison_data.get('sharpe', 0.0),
                    'max_drawdown': comparison_data.get('max_drawdown_account', 0.0) * 100,  # Convert to percentage
                    'avg_profit': comparison_data.get('profit_mean_pct', 0.0),
                    'cagr': comparison_data.get('cagr', 0.0) * 100,  # Convert to percentage
                    'expectancy': comparison_data.get('expectancy', 0.0),
                    'sortino': comparison_data.get('sortino', 0.0),
                    'calmar': comparison_data.get('calmar', 0.0),
                    'sqn': comparison_data.get('sqn', 0.0),
                    'winning_trades': comparison_data.get('wins', 0),
                    'losing_trades': comparison_data.get('losses', 0),
                    'avg_duration': comparison_data.get('duration_avg', '')
                })
                
                # Extract backtest dates and other info from root level if available
                if 'backtest_start' in backtest_data:
                    metrics['backtest_start'] = backtest_data.get('backtest_start', '')
                    metrics['backtest_end'] = backtest_data.get('backtest_end', '')
                    metrics['market_change'] = backtest_data.get('market_change', 0.0)
                
                # Extract best/worst pairs from root level if available
                best_pair_data = backtest_data.get('best_pair', {})
                worst_pair_data = backtest_data.get('worst_pair', {})
                if best_pair_data:
                    metrics['best_pair'] = best_pair_data.get('key', '')
                if worst_pair_data:
                    metrics['worst_pair'] = worst_pair_data.get('key', '')
                
                logger.debug(f"Parsed metrics for {strategy_name}: {metrics['total_profit_percent']:.2f}% return, {metrics['total_trades']} trades")
                return metrics
            
            # Check if this is the direct format with metrics at root level (fallback)
            elif 'total_trades' in backtest_data:
                # Direct format - metrics at root level
                metrics.update({
                    'total_trades': backtest_data.get('total_trades', 0),
                    'total_profit_percent': backtest_data.get('profit_total_pct', 0.0),
                    'total_profit_abs': backtest_data.get('profit_total_abs', 0.0),
                    'win_rate': backtest_data.get('winrate', 0.0) * 100,  # Convert to percentage
                    'profit_factor': backtest_data.get('profit_factor', 0.0),
                    'sharpe_ratio': backtest_data.get('sharpe', 0.0),
                    'max_drawdown': backtest_data.get('max_drawdown_account', 0.0) * 100,  # Convert to percentage
                    'avg_profit': backtest_data.get('profit_mean_pct', 0.0),
                    'cagr': backtest_data.get('cagr', 0.0),
                    'expectancy': backtest_data.get('expectancy', 0.0),
                    'sortino': backtest_data.get('sortino', 0.0),
                    'calmar': backtest_data.get('calmar', 0.0),
                    'sqn': backtest_data.get('sqn', 0.0),
                    'backtest_start': backtest_data.get('backtest_start', ''),
                    'backtest_end': backtest_data.get('backtest_end', ''),
                    'market_change': backtest_data.get('market_change', 0.0)
                })
                
                # Extract best/worst pairs if available
                best_pair_data = backtest_data.get('best_pair', {})
                worst_pair_data = backtest_data.get('worst_pair', {})
                if best_pair_data:
                    metrics['best_pair'] = best_pair_data.get('key', '')
                if worst_pair_data:
                    metrics['worst_pair'] = worst_pair_data.get('key', '')
                
                # Calculate wins/losses from winrate and total trades
                total_trades = metrics['total_trades']
                winrate = metrics['win_rate'] / 100.0
                metrics['winning_trades'] = int(total_trades * winrate)
                metrics['losing_trades'] = total_trades - metrics['winning_trades']
                
                # Extract average duration if available
                avg_duration = backtest_data.get('holding_avg', '')
                metrics['avg_duration'] = avg_duration
                
                logger.debug(f"Parsed metrics for {strategy_name}: {metrics['total_profit_percent']:.2f}% return, {metrics['total_trades']} trades")
                return metrics
            
            else:
                logger.warning(f"Unrecognized backtest data structure in {strategy_dir}")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing JSON data for {strategy_dir.name}: {e}")
            return None
    
    def discover_all_successful_strategies(self) -> Tuple[List[str], Dict[str, Dict]]:
        """
        Discover all strategies that have successful backtest results.
        
        Returns:
            Tuple of (strategy_names_list, results_dict)
        """
        successful_strategies = []
        results = {}
        
        if not self.results_dir.exists():
            logger.warning(f"Results directory not found: {self.results_dir}")
            return [], {}
        
        success_count = 0
        
        # Scan all strategy directories for backtest results
        for strategy_dir in self.results_dir.iterdir():
            if not strategy_dir.is_dir() or strategy_dir.name in ['individual_results']:
                continue
            
            # Try to parse JSON backtest data
            metrics = self.parse_strategy_json_data(strategy_dir)
            if metrics:
                strategy_name = metrics['strategy']
                successful_strategies.append(strategy_name)
                results[strategy_name] = metrics
                success_count += 1
                logger.debug(f"Found successful strategy: {strategy_name}")
        
        # Also check the individual_results directory for any cached results
        if self.individual_results_dir.exists():
            # Load successful results from individual files
            for result_file in self.individual_results_dir.glob("*_result.json"):
                try:
                    with open(result_file, 'r') as f:
                        result = json.load(f)
                        strategy_name = result.get('strategy', result_file.stem.replace('_result', ''))
                        if strategy_name not in results:  # Don't override directory-based results
                            successful_strategies.append(strategy_name)
                            results[strategy_name] = result
                            success_count += 1
                            logger.debug(f"Found cached successful strategy: {strategy_name}")
                except Exception as e:
                    logger.warning(f"Could not load result from {result_file}: {e}")
        
        # Remove duplicates and sort
        successful_strategies = sorted(list(set(successful_strategies)))
        
        logger.info(f"Found {len(successful_strategies)} previously successful strategies")
        return successful_strategies, results
    
    def get_failed_strategies(self) -> List[Dict]:
        """Get list of strategies that failed during backtesting."""
        failed_strategies = []
        
        if not self.results_dir.exists():
            return failed_strategies
        
        # Scan strategy directories for failed result indicators
        for strategy_dir in self.results_dir.iterdir():
            if not strategy_dir.is_dir() or strategy_dir.name in ['individual_results']:
                continue
            
            # Check if this strategy has successful results
            metrics = self.parse_strategy_json_data(strategy_dir)
            if not metrics:
                # If no successful results found, check for failed result indicators
                failed_indicators = list(strategy_dir.glob("*_failed*")) + list(strategy_dir.glob("*error*"))
                if failed_indicators:
                    failed_result = {
                        'strategy': strategy_dir.name,
                        'error': 'Backtest failed',
                        'failed_timestamp': datetime.now().isoformat()
                    }
                    failed_strategies.append(failed_result)
                    logger.debug(f"Detected failed strategy: {strategy_dir.name}")
        
        # Also check the individual_results directory for cached failed results
        if self.individual_results_dir.exists():
            for failed_file in self.individual_results_dir.glob("*_failed.json"):
                try:
                    with open(failed_file, 'r') as f:
                        failed_result = json.load(f)
                        strategy_name = failed_result.get('strategy', failed_file.stem.replace('_failed', ''))
                        # Only add if we don't already have this strategy
                        if not any(fs.get('strategy') == strategy_name for fs in failed_strategies):
                            failed_strategies.append(failed_result)
                            logger.debug(f"Found cached failed strategy: {strategy_name}")
                except Exception as e:
                    logger.warning(f"Could not load failed result from {failed_file}: {e}")
        
        return failed_strategies
    
    def collect_all_results(self) -> Tuple[Dict[str, Dict], List[Dict]]:
        """
        Collect all existing results from strategy directories.
        
        Returns:
            Tuple of (successful_results_dict, failed_strategies_list)
        """
        successful_strategies, results = self.discover_all_successful_strategies()
        failed_strategies = self.get_failed_strategies()
        
        logger.info(f"📊 Found {len(results)} successful and {len(failed_strategies)} failed backtest results")
        return results, failed_strategies


def get_strategy_results_utils(results_dir: str = "user_data/backtest_results") -> StrategyResultsUtils:
    """Factory function to create a StrategyResultsUtils instance."""
    return StrategyResultsUtils(results_dir)


def discover_successful_strategies(results_dir: str = "user_data/backtest_results") -> List[str]:
    """
    Convenience function to get just the list of successful strategy names.
    
    Args:
        results_dir: Directory containing backtest results
        
    Returns:
        List of successful strategy names
    """
    utils = StrategyResultsUtils(results_dir)
    successful_strategies, _ = utils.discover_all_successful_strategies()
    return successful_strategies


def get_all_strategy_results(results_dir: str = "user_data/backtest_results") -> Tuple[Dict[str, Dict], List[Dict]]:
    """
    Convenience function to get all strategy results.
    
    Args:
        results_dir: Directory containing backtest results
        
    Returns:
        Tuple of (successful_results_dict, failed_strategies_list)
    """
    utils = StrategyResultsUtils(results_dir)
    return utils.collect_all_results() 