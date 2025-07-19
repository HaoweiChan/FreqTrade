#!/usr/bin/env python3
"""
Freqtrade Strategy Interface Updater
This script updates all strategies from the old freqtrade interface (v2) to the new interface (v3).
"""

import os
import re
import shutil
import logging
from typing import List
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StrategyUpdater:
    def __init__(self, strategies_dir: str = "user_data/strategies"):
        self.strategies_dir = Path(strategies_dir)
        self.backup_dir = self.strategies_dir.parent / "strategies_backup"
        self.updated_count = 0
        self.failed_count = 0
        
        # Method name mappings (old -> new)
        self.method_mappings = {
            'populate_buy_trend': 'populate_entry_trend',
            'populate_sell_trend': 'populate_exit_trend',
            'custom_sell': 'custom_exit',
            'check_buy_timeout': 'check_entry_timeout',
            'check_sell_timeout': 'check_exit_timeout',
        }
        
        # Column name mappings (old -> new)
        self.column_mappings = {
            'buy': 'enter_long',
            'sell': 'exit_long',
            'buy_tag': 'enter_tag',
            'sell_tag': 'exit_tag',
        }
        
        # Strategy property mappings (old -> new)
        self.property_mappings = {
            'use_sell_signal': 'use_exit_signal',
            'sell_profit_only': 'exit_profit_only',
            'sell_profit_offset': 'exit_profit_offset',
            'ignore_roi_if_buy_signal': 'ignore_roi_if_entry_signal',
        }
        
        # Order types mappings (old -> new)
        self.order_types_mappings = {
            'buy': 'entry',
            'sell': 'exit',
            'emergencysell': 'emergency_exit',
            'forcesell': 'force_exit',
            'forcebuy': 'force_entry',
        }
        
        # Time in force mappings (old -> new)
        self.time_in_force_mappings = {
            'buy': 'entry',
            'sell': 'exit',
        }
        
        # Callback parameter updates
        self.callback_updates = {
            'custom_stake_amount': {
                'add_params': ['side: str'],
                'param_order': ['pair', 'current_time', 'current_rate', 'proposed_stake', 'min_stake', 'max_stake', 'entry_tag', 'side']
            },
            'confirm_trade_entry': {
                'add_params': ['side: str'],
                'param_order': ['pair', 'order_type', 'amount', 'rate', 'time_in_force', 'current_time', 'entry_tag', 'side']
            },
            'confirm_trade_exit': {
                'replace_params': {'sell_reason': 'exit_reason'},
                'param_order': ['pair', 'trade', 'order_type', 'amount', 'rate', 'time_in_force', 'exit_reason', 'current_time']
            },
            'custom_entry_price': {
                'add_params': ['side: str'],
                'param_order': ['pair', 'current_time', 'proposed_rate', 'entry_tag', 'side']
            },
            'custom_stoploss': {
                'add_params': ['after_fill: bool'],
                'param_order': ['pair', 'trade', 'current_time', 'current_rate', 'current_profit', 'after_fill']
            }
        }
        
    def create_backup(self):
        """Create a backup of all strategies before updating."""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        shutil.copytree(self.strategies_dir, self.backup_dir)
        logger.info(f"Created backup of strategies in {self.backup_dir}")
    
    def find_strategy_files(self) -> List[Path]:
        """Find all Python strategy files."""
        strategy_files = []
        for root, dirs, files in os.walk(self.strategies_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    strategy_files.append(Path(root) / file)
        return strategy_files
    
    def update_interface_version(self, content: str) -> str:
        """Update INTERFACE_VERSION to 3."""
        # Look for existing INTERFACE_VERSION
        version_pattern = r'INTERFACE_VERSION\s*=\s*[0-9]+'
        if re.search(version_pattern, content):
            content = re.sub(version_pattern, 'INTERFACE_VERSION = 3', content)
        else:
            # Add INTERFACE_VERSION if not present
            class_pattern = r'(class\s+\w+\s*\([^)]*IStrategy[^)]*\)\s*:)'
            if re.search(class_pattern, content):
                content = re.sub(class_pattern, r'\1\n    INTERFACE_VERSION = 3\n', content)
        
        return content
    
    def update_method_names(self, content: str) -> str:
        """Update method names from old to new interface."""
        for old_method, new_method in self.method_mappings.items():
            # Update method definitions
            pattern = rf'def\s+{old_method}\s*\('
            replacement = f'def {new_method}('
            content = re.sub(pattern, replacement, content)
            
            # Update method calls
            pattern = rf'self\.{old_method}\s*\('
            replacement = f'self.{new_method}('
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def update_column_names(self, content: str) -> str:
        """Update dataframe column names from old to new interface."""
        for old_col, new_col in self.column_mappings.items():
            # Update column assignments like dataframe['buy'] = 1
            pattern = rf"dataframe\[(['\"]){old_col}\1\]"
            replacement = f"dataframe[\\1{new_col}\\1]"
            content = re.sub(pattern, replacement, content)
            
            # Update column assignments in lists like ['buy', 'buy_tag']
            pattern = rf"(['\"]){old_col}\1"
            replacement = f"\\1{new_col}\\1"
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def update_property_names(self, content: str) -> str:
        """Update strategy property names from old to new interface."""
        for old_prop, new_prop in self.property_mappings.items():
            # Update property assignments
            pattern = rf'{old_prop}\s*='
            replacement = f'{new_prop} ='
            content = re.sub(pattern, replacement, content)
            
            # Update property references
            pattern = rf'self\.{old_prop}'
            replacement = f'self.{new_prop}'
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def update_order_types(self, content: str) -> str:
        """Update order_types dictionary from old to new interface."""
        for old_key, new_key in self.order_types_mappings.items():
            # Update dictionary keys
            pattern = rf'(["\']){old_key}\1\s*:'
            replacement = f'\\1{new_key}\\1:'
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def update_time_in_force(self, content: str) -> str:
        """Update order_time_in_force dictionary from old to new interface."""
        for old_key, new_key in self.time_in_force_mappings.items():
            # Update dictionary keys in order_time_in_force
            pattern = rf'(["\']){old_key}\1\s*:'
            replacement = f'\\1{new_key}\\1:'
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def update_callback_signatures(self, content: str) -> str:
        """Update callback method signatures to include new parameters."""
        for method_name, updates in self.callback_updates.items():
            # Find method definition
            method_pattern = rf'def\s+{method_name}\s*\([^)]*\):'
            method_match = re.search(method_pattern, content)
            
            if method_match:
                # Extract current parameters
                full_match = method_match.group(0)
                params_start = full_match.find('(') + 1
                params_end = full_match.rfind(')')
                current_params = full_match[params_start:params_end]
                
                # Update parameters based on configuration
                if 'add_params' in updates:
                    for param in updates['add_params']:
                        if param not in current_params:
                            if current_params.strip() and not current_params.endswith(','):
                                current_params += ', '
                            current_params += param
                
                if 'replace_params' in updates:
                    for old_param, new_param in updates['replace_params'].items():
                        current_params = current_params.replace(old_param, new_param)
                
                # Reconstruct method signature
                new_signature = f'def {method_name}({current_params}):'
                content = content.replace(full_match, new_signature)
        
        return content
    
    def update_helper_functions(self, content: str) -> str:
        """Update helper function calls to include new parameters."""
        # Update stoploss_from_open calls
        pattern = r'stoploss_from_open\s*\(\s*([^,)]+)\s*,\s*([^,)]+)\s*\)'
        replacement = r'stoploss_from_open(\1, \2, is_short=trade.is_short)'
        content = re.sub(pattern, replacement, content)
        
        # Update stoploss_from_absolute calls
        pattern = r'stoploss_from_absolute\s*\(\s*([^,)]+)\s*,\s*([^,)]+)\s*\)'
        replacement = r'stoploss_from_absolute(\1, \2, is_short=trade.is_short)'
        content = re.sub(pattern, replacement, content)
        
        return content
    
    def update_trade_properties(self, content: str) -> str:
        """Update trade object property references."""
        # Update sell_reason to exit_reason
        content = re.sub(r'trade\.sell_reason', 'trade.exit_reason', content)
        
        # Update nr_of_successful_buys to nr_of_successful_entries
        content = re.sub(r'trade\.nr_of_successful_buys', 'trade.nr_of_successful_entries', content)
        
        return content
    
    def update_imports(self, content: str) -> str:
        """Update import statements to include new interface elements."""
        # Check if stoploss_from_open or stoploss_from_absolute are used
        if 'stoploss_from_open' in content or 'stoploss_from_absolute' in content:
            # Add imports if not present
            if 'from freqtrade.strategy import' in content:
                # Add to existing import
                import_pattern = r'from freqtrade\.strategy import ([^)]+)'
                import_match = re.search(import_pattern, content)
                if import_match:
                    imports = import_match.group(1)
                    if 'stoploss_from_open' not in imports:
                        imports += ', stoploss_from_open'
                    if 'stoploss_from_absolute' not in imports:
                        imports += ', stoploss_from_absolute'
                    content = re.sub(import_pattern, f'from freqtrade.strategy import {imports}', content)
        
        return content
    
    def update_unfilledtimeout(self, content: str) -> str:
        """Update unfilledtimeout configuration from old to new interface."""
        # Update buy -> entry, sell -> exit
        content = re.sub(r'(["\'])buy\1\s*:', r'\1entry\1:', content)
        content = re.sub(r'(["\'])sell\1\s*:', r'\1exit\1:', content)
        
        return content
    
    def update_strategy_file(self, file_path: Path) -> bool:
        """Update a single strategy file."""
        try:
            logger.info(f"Updating strategy: {file_path}")
            
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply all updates
            original_content = content
            
            content = self.update_interface_version(content)
            content = self.update_method_names(content)
            content = self.update_column_names(content)
            content = self.update_property_names(content)
            content = self.update_order_types(content)
            content = self.update_time_in_force(content)
            content = self.update_callback_signatures(content)
            content = self.update_helper_functions(content)
            content = self.update_trade_properties(content)
            content = self.update_imports(content)
            content = self.update_unfilledtimeout(content)
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"✅ Updated: {file_path}")
                return True
            else:
                logger.info(f"ℹ️  No changes needed: {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to update {file_path}: {str(e)}")
            return False
    
    def update_all_strategies(self):
        """Update all strategy files."""
        logger.info("Starting strategy interface update process...")
        
        # Create backup
        self.create_backup()
        
        # Find all strategy files
        strategy_files = self.find_strategy_files()
        logger.info(f"Found {len(strategy_files)} strategy files to update")
        
        # Update each file
        for file_path in strategy_files:
            if self.update_strategy_file(file_path):
                self.updated_count += 1
            else:
                self.failed_count += 1
        
        # Summary
        logger.info(f"\n📊 UPDATE SUMMARY:")
        logger.info(f"Total files processed: {len(strategy_files)}")
        logger.info(f"Successfully updated: {self.updated_count}")
        logger.info(f"Failed updates: {self.failed_count}")
        logger.info(f"Backup created at: {self.backup_dir}")
        
        if self.failed_count > 0:
            logger.warning(f"⚠️  {self.failed_count} files failed to update. Check the logs for details.")
        else:
            logger.info("🎉 All strategies updated successfully!")
    
    def verify_updates(self):
        """Verify that updates were applied correctly."""
        logger.info("Verifying strategy updates...")
        
        strategy_files = self.find_strategy_files()
        issues = []
        
        for file_path in strategy_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for old method names
                for old_method in self.method_mappings.keys():
                    if f'def {old_method}(' in content:
                        issues.append(f"{file_path}: Still contains old method {old_method}")
                
                # Check for old column names in assignments
                for old_col in self.column_mappings.keys():
                    if f"'{old_col}'" in content or f'"{old_col}"' in content:
                        # This is a basic check - might have false positives
                        if f"dataframe['{old_col}']" in content or f'dataframe["{old_col}"]' in content:
                            issues.append(f"{file_path}: Still contains old column {old_col}")
                
            except Exception as e:
                issues.append(f"{file_path}: Error reading file - {str(e)}")
        
        if issues:
            logger.warning(f"Found {len(issues)} potential issues:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("✅ Verification complete - no issues found!")

def main():
    """Main function to run the strategy updater."""
    updater = StrategyUpdater()
    
    # Update all strategies
    updater.update_all_strategies()
    
    # Verify updates
    updater.verify_updates()
    
    print("\n" + "="*60)
    print("STRATEGY UPDATE COMPLETE")
    print("="*60)
    print(f"📁 Backup location: {updater.backup_dir}")
    print(f"📊 Updated strategies: {updater.updated_count}")
    print(f"❌ Failed updates: {updater.failed_count}")
    print("\nNext steps:")
    print("1. Test a few strategies with 'freqtrade list-strategies'")
    print("2. Run compatibility checker: 'python strategy_tools/strategy_compatibility_checker.py'")
    print("3. Try backtesting a strategy to verify it works")
    print("4. If issues occur, restore from backup and check logs")

if __name__ == "__main__":
    main() 