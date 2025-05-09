import asyncio
import importlib.util
import sys
import os
import random
import logging
from datetime import datetime, timedelta
from colorama import Fore, Style, init
from utils import data

# Initialize colorama
init(autoreset=True)

logger = logging.getLogger("MultiDexRunner")

# Configuration
SRC_FOLDER = "src"  # Folder containing the scripts
SCRIPTS = data["SCRIPTS"]  # Script names without .py extension
BORDER_WIDTH = 80
MIN_HOURS = 20
MAX_HOURS = 24
MIN_INTERVAL = 1  # Minimum minutes between different script executions
MAX_INTERVAL = 2  # Maximum minutes between different script executions


def print_border(message, color=Fore.WHITE):
    """Print a centered message with color."""
    print(f"{color}{message:^{BORDER_WIDTH}}{Style.RESET_ALL}")


async def run_script(script_name):
    """Run a single script module from the src folder."""
    try:
        # Construct the file path
        script_path = os.path.join(SRC_FOLDER, f"{script_name}.py")

        # Check if the file exists
        if not os.path.exists(script_path):
            logger.error(f"Script file not found: {script_path}")
            print_border(f"ERROR: {script_path} not found", Fore.RED)
            return None

        # Import the module from file path
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        if spec is None:
            logger.error(f"Cannot load spec for {script_path}")
            print_border(f"ERROR: Cannot load {script_path}", Fore.RED)
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[script_name] = module
        spec.loader.exec_module(module)

        # Check if the module has a run function
        if hasattr(module, "run"):
            logger.info(f"Running {script_name}...")
            print_border(f"RUNNING {script_name.upper()}", Fore.CYAN)

            # Run the script's main function
            result = await module.run()

            logger.info(f"Completed {script_name}")
            return result
        else:
            logger.error(f"No run function found in {script_name}.py")
            print_border(f"ERROR: No run function in {script_name}.py", Fore.RED)
            return None
    except Exception as e:
        logger.error(f"Error running {script_name}: {str(e)}")
        print_border(f"ERROR in {script_name}: {str(e)}", Fore.RED)
        return None


async def schedule_scripts():
    """Run all scripts in sequence with intervals, then wait for next cycle."""
    execution_count = 0

    while True:
        execution_count += 1
        current_time = datetime.now()

        print(f"\n{Fore.MAGENTA}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
        print_border(f"EXECUTION CYCLE #{execution_count} - {current_time.strftime('%Y-%m-%d %H:%M:%S')}", Fore.MAGENTA)
        print(f"{Fore.MAGENTA}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")

        random.shuffle(SCRIPTS)
        # Run each script with a random interval between them
        for i, script_name in enumerate(SCRIPTS):
            await run_script(script_name)

            # Add a random interval between scripts (except after the last one)
            if i < len(SCRIPTS) - 1:
                minutes = random.uniform(MIN_INTERVAL, MAX_INTERVAL)
                wait_msg = f"Waiting {minutes:.2f} minutes before next script..."
                print(f"{Fore.YELLOW}⏳ {wait_msg:^{BORDER_WIDTH}}{Style.RESET_ALL}")
                await asyncio.sleep(minutes * 60)

        # Calculate the next run cycle (between MIN_HOURS-MAX_HOURS)
        hours = random.uniform(MIN_HOURS, MAX_HOURS)
        next_run_delay = hours * 3600  # Convert hours to seconds
        next_run_time = current_time + timedelta(seconds=next_run_delay)

        # Display next run information
        print(f"\n{Fore.CYAN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")
        next_run_msg = f"NEXT CYCLE: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')} (in {hours:.2f} hours)"
        print_border(next_run_msg, Fore.CYAN)
        print(f"{Fore.CYAN}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")

        logger.info(f"Completed execution cycle #{execution_count}")
        logger.info(f"Next cycle scheduled for {next_run_time.strftime('%Y-%m-%d %H:%M:%S')} (in {hours:.2f} hours)")

        # Sleep until next run cycle
        await asyncio.sleep(next_run_delay)


async def main():
    """Main entry point."""
    # Ensure src directory exists
    if not os.path.isdir(SRC_FOLDER):
        logger.critical(f"Source folder '{SRC_FOLDER}' not found!")
        print(f"{Fore.RED}ERROR: Source folder '{SRC_FOLDER}' not found!{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}Starting Multi-DEX Runner...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Looking for scripts in: {SRC_FOLDER}/{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Running scripts: {', '.join(SCRIPTS)}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Press Ctrl+C to stop the script{Style.RESET_ALL}")

    await schedule_scripts()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Script stopped by user{Style.RESET_ALL}")
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        print(f"\n{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")