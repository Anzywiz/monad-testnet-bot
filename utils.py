import asyncio
import json
from web3 import Web3, AsyncWeb3
import requests
import random
import os
from pathlib import Path
from logger import color_print
from proxies import get_free_proxy
from headers import get_phantom_headers

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))


def get_config_path():
    # Find the base directory (where config.json should be)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # For utils.py at the base level
    if os.path.basename(base_dir) != 'monad-testnet-bot':
        base_dir = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_dir, 'config.json')


# Load data from the CONFIG file
try:
    with open(get_config_path(), "r") as file:
        data = json.load(file)
except FileNotFoundError:
    raise FileNotFoundError(f"config.json file does not exist. Create one")
except json.JSONDecodeError:
    raise ValueError(f"The config file is not a valid JSON file.")

# load private keys
try:
    with open(BASE_DIR/"private_keys.txt", "r") as f:
        private_keys_ = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    raise FileNotFoundError("File private_keys.txt not found!")

if not private_keys_:
    raise Exception("ERROR: No private keys found in private_keys.txt!", "RED")

# Get range from config
start, end = data.get("PRIVATE_KEYS_RANGE", [0, len(private_keys_)])

# Validate range
if not (0 <= start < end <= len(private_keys_)):
    print("Invalid PRIVATE_KEYS_RANGE, using full list.")
    selected_keys = private_keys_
else:
    selected_keys = private_keys_[start-1:end]

private_keys = selected_keys

RPC_URL = "https://testnet-rpc.monad.xyz"
PROXIES = data["PROXIES"]
GITHUB_USERNAME = data["GITHUB_USERNAME"]

if PROXIES:
    color_print(f"Proxies found in config file", 'GREEN')
else:
    color_print(f"Proxies NOT found in config file!", "RED")
    reply = input("Do you like to proceed with free proxies. Free proxies might be buggy (y/n): ")


def verify_github_star(repo_url, config_path='config.json'):
    """
    Verify if the user has starred a specific GitHub repository.

    Args:
        repo_url (str): The full GitHub repository URL to check for starring
        config_path (str): Path to the configuration file

    Returns:
        bool: True if the user has starred the repository, False otherwise
    """
    try:
        # Read GitHub username from config file
        if not os.path.exists(config_path):
            print(f"❌ Config file not found at {config_path}")
            return False

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Extract GitHub username from config
        github_username = GITHUB_USERNAME

        if not github_username:
            print("❌ GitHub username not found in config file")
            return False

        # Extract repository owner and name from the URL
        parts = repo_url.rstrip('/').split('/')
        repo_owner = parts[-2]
        repo_name = parts[-1]

        # GitHub API endpoint to get stargazers
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/stargazers"

        # Make API request to get stargazers
        response = requests.get(api_url)

        # Check if the request was successful
        if response.status_code == 200:
            # Get list of stargazers
            stargazers = response.json()

            # Check if the user's username is in the list of stargazers
            is_starred = any(star['login'].lower() == github_username.lower() for star in stargazers)

            if is_starred:
                color_print(f"✅ Verified! {github_username} has starred {repo_url}", "GREEN")
                return True
            else:
                color_print(f"❌ Error: {github_username} has not starred {repo_url}", "RED")
                return False
        else:
            color_print(f"❌ Failed to retrieve stargazers. Status code: {response.status_code}", "RED")
            return False

    except requests.RequestException as e:
        color_print(f"Network error: {e}", "RED")
        return False
    except json.JSONDecodeError:
        color_print(f"❌ Error parsing config file at {config_path}", "RED")
        return False
    except Exception as e:
        color_print(f"An unexpected error occurred: {e}", "RED")
        return False


def get_web3_connection(use_async=False):
    """Get Web3 connection with optional async support.

    Args:
        use_async (bool): Whether to use AsyncWeb3 instead of regular Web3

    Returns:
        Web3 or AsyncWeb3 instance
    """
    request_kwargs = {"headers": get_phantom_headers()}

    if PROXIES:
        request_kwargs["proxies"] = {'https': PROXIES, 'http': PROXIES}
    else:
        if reply.lower() == 'y':
            free_proxies = get_free_proxy()['proxy']
            request_kwargs["proxies"] = free_proxies

    if use_async:
        # For AsyncWeb3, convert 'proxies' to 'proxy'
        if "proxies" in request_kwargs:
            # Get the proxy value (either from dict or directly)
            proxy_value = request_kwargs["proxies"]
            if isinstance(proxy_value, dict) and "http" in proxy_value:
                proxy_value = proxy_value["http"]

            # Replace 'proxies' with 'proxy'
            request_kwargs["proxy"] = proxy_value
            del request_kwargs["proxies"]

        # For AsyncWeb3
        provider = AsyncWeb3.AsyncHTTPProvider(RPC_URL, request_kwargs=request_kwargs)
        return AsyncWeb3(provider)
    else:
        # For regular Web3
        provider = Web3.HTTPProvider(RPC_URL, request_kwargs=request_kwargs)
        return Web3(provider)


async def timeout(start=60, end=300):
    time_out = random.randint(start, end)

    hours = time_out // 3600
    minutes = (time_out % 3600) // 60
    seconds = time_out % 60

    if hours > 0:
        time_str = f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        time_str = f"{minutes}m {seconds}s"
    else:
        time_str = f"{seconds}s"

    color_print(f"⏳ Waiting {time_str} ...", "GREEN", style="BRIGHT")
    await asyncio.sleep(time_out)
