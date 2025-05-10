from colorama import Fore, Back, Style
import colorlog
import logging

def color_print(text, color="BLUE", background=None, style=None):
    """
        # Example usage:
    color_print("This is blue text", "BLUE")
    color_print("This is red with a yellow background", "RED", "YELLOW")
    color_print("This is bright green text", "GREEN", style="BRIGHT")
    """

    colors = {
        "BLACK": Fore.BLACK, "RED": Fore.RED, "GREEN": Fore.GREEN,
        "YELLOW": Fore.YELLOW, "BLUE": Fore.BLUE, "MAGENTA": Fore.MAGENTA,
        "CYAN": Fore.CYAN, "WHITE": Fore.WHITE, "RESET": Fore.RESET
    }

    backgrounds = {
        "BLACK": Back.BLACK, "RED": Back.RED, "GREEN": Back.GREEN,
        "YELLOW": Back.YELLOW, "BLUE": Back.BLUE, "MAGENTA": Back.MAGENTA,
        "CYAN": Back.CYAN, "WHITE": Back.WHITE, "RESET": Back.RESET
    }

    styles = {
        "DIM": Style.DIM, "NORMAL": Style.NORMAL,
        "BRIGHT": Style.BRIGHT, "RESET": Style.RESET_ALL
    }

    color_code = colors.get(color.upper(), Fore.RESET)
    bg_code = backgrounds.get(background.upper(), "") if background else ""
    style_code = styles.get(style.upper(), "") if style else ""

    print(f"{style_code}{bg_code}{color_code}{text}{Style.RESET_ALL}")


# First, define a SUCCESS level
SUCCESS_LEVEL = 25  # Between INFO (20) and WARNING (30)
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


# Create a success method for Logger class
def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)


# Add the success method to the Logger class
logging.Logger.success = success

formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)s: %(asctime)s: %(message)s',
    log_colors={
        'DEBUG': 'green',
        'INFO': 'cyan',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
        'SUCCESS': 'green,bold'  # Add color for SUCCESS level
    },
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = colorlog.StreamHandler()
handler.setFormatter(formatter)

file_handler = logging.FileHandler("monad_bot.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = colorlog.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(file_handler)