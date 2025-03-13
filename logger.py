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


formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)s: %(asctime)s: %(message)s',
    log_colors={
        'DEBUG': 'green',
        'INFO': 'cyan',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white'
    },
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = colorlog.StreamHandler()
handler.setFormatter(formatter)

logger = colorlog.getLogger()
logger.addHandler(handler)
logger.setLevel(colorlog.INFO)
