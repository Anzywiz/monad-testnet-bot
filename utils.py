import asyncio
import os
import json
from web3 import Web3
import random
import requests
import logging

from src.proxies import get_free_proxy, get_phantom_headers
from src.swapper import MonadSwapper
from src.staker import MonadStaker
from src.ai_craft_fun import AiCraftFun
from web3.exceptions import Web3RPCError
from src.logger import color_print


# Load data from the CONFIG file
try:
    with open('config.json', "r") as file:
        data = json.load(file)
except FileNotFoundError:
    raise FileNotFoundError(f"config.json file does not exist. Create one")
except json.JSONDecodeError:
    raise ValueError(f"The config file is not a valid JSON file.")


RPC_URL = "https://testnet-rpc.monad.xyz"
FUNDER_PRIVATE_KEY = data["FUNDER_PRIVATE_KEY"]
FUND_AMT = data["FUND_AMOUNT"]
SWAP_CYCLES = data["DAILY_SWAP_CYCLES"]
STAKE_CYCLES = data["STAKE_CYCLES"]
PROXIES = data["PROXIES"]
GITHUB_USERNAME = data["GITHUB_USERNAME"]


if PROXIES:
    color_print(f"Proxies found in config file", 'GREEN')
else:
    color_print(f"Proxies NOT found in config file!", "RED")
    reply = input("Do you like to proceed with free proxies. Free proxies might be buggy (y/n): ")


def get_random_stake_amount():
    # Generate a random value between 0.0001 and 0.001
    rand_int = random.randint(1, 100)
    random_swap_amt = float(f"0.000{rand_int}")
    return random_swap_amt


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


def get_web3_connection():
    if PROXIES:
        web3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"headers": get_phantom_headers(), "proxies": {'https': PROXIES, 'http': PROXIES}}))
    else:
        if reply.lower() == 'y':
            free_proxies = get_free_proxy()['proxy']
            web3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"proxies": free_proxies, "headers": get_phantom_headers()}))
        else:
            web3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"headers": get_phantom_headers()}))
    return web3


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

    color_print(f"Awaiting {time_str} timeout...", "GREEN", style="BRIGHT")
    await asyncio.sleep(time_out)


async def swap_tokens(private_key, cycles=SWAP_CYCLES):
    count = 0
    while True:  # Infinite loop, till you interrupt
        try:
            # Initialize the swapper
            swapper = MonadSwapper(get_web3_connection(), private_key)
            # Display balances for a specific address
            swapper.display_wallet_balances()

            try:
                rand_int = random.randint(1, 100)
                random_swap_amt = f"0.000{rand_int}"
                to_tokens = ['CHOG', 'DAK', 'YAKI', 'WMON', "USDC"]
                random_token = random.choice(to_tokens)

                # Execute a swap (will sign and broadcast the transaction)
                tx_hash = swapper.execute_swap(
                    amount=float(random_swap_amt),
                    from_token="MON",
                    to_token=random_token
                )
                count += 1
                logging.info(f"Account {swapper.display_address}: Swap count: {count}/{cycles}..")

                # Check if cycle is complete
                if count >= cycles:
                    logging.info(f"Account {swapper.display_address}: Full Swap cycle complete.")
                    await timeout(60 * 60 * 18, 60 * 60 * 24)  # Long wait between cycles
                    count = 0  # Reset counter after waiting
                else:
                    await timeout()  # Normal wait between swaps

            except Web3RPCError as e:
                if 'Signer had insufficient balance' in str(e):
                    logging.warning(
                        f"Account {swapper.display_address}: Signer had insufficient balance. Funding from Fund wallet..")
                    # initialise funder
                    funder = MonadSwapper(get_web3_connection(), FUNDER_PRIVATE_KEY)
                    funder.send_base_tokens(swapper.wallet_address, FUND_AMT)
                else:
                    logging.error(f"Error {e}. Trying again..")
                    await asyncio.sleep(5)

        except Exception as e:
            color_print(f"An error occurred within the infinite loop\n{e}", "RED")
            color_print(f"Restarting Monad swapper...", "MAGENTA")
            await asyncio.sleep(1 * 60 * 60)


async def stake_token(private_key, cycles=STAKE_CYCLES):
    count = 0
    while True:  # Infinite loop, till you interrupt
        try:
            # Initialize the swapper
            staker = MonadStaker(get_web3_connection(), private_key)

            try:
                # Define possible staking methods
                staking_methods = ['magma_stake', 'apriori_stake', 'kintsu_stake']

                method_name = random.choices(staking_methods, weights=[0.49, 0.48, 0.03])[0]

                if method_name == "kintsu_stake":
                    # Get a random amount greater than 0.01
                    rand_int = random.randint(1, 3)
                    amount = float(f"0.0{rand_int}")
                else:
                    amount = get_random_stake_amount()

                # Get the method from the staker object
                staking_method = getattr(staker, method_name)

                # Call the selected staking method with the amount
                color_print(f"Prepping to stake {amount} MON on {method_name.split('_')[0]}")
                staking_method(amount)
                if method_name == "magma_stake":
                    await timeout(30, 120)
                    color_print(f"Prepping to Unstake {amount} MON on {method_name.split('_')[0]}")
                    staker.magma_unstake(amount)
                # elif method_name == "kintsu_stake":
                #     await timeout(30, 120)
                #     # You cannot unstake on Kinstu yet
                #     color_print(f"Prepping to Unstake {amount} sMON on {method_name.split('_')[0]} via Monorail swap")
                #     tx_hash = staker.execute_swap(
                #         amount=float(amount),
                #         from_token="sMON",
                #         to_token="MON")

                count += 1
                logging.info(f"Account {staker.display_address}: Stake count: {count}/{cycles}..")

                if count >= cycles:
                    logging.info(f"Account {staker.display_address}: Full Stake cycle complete.")
                    await timeout(60 * 60 * 20, 60 * 60 * 24)
                    count = 0  # Reset counter after waiting
                else:
                    await timeout(60, 200)

            except Web3RPCError as e:
                # Error handling as before
                if 'Signer had insufficient balance' in str(e):
                    logging.warning(
                        f"Account {staker.display_address}: Signer had insufficient balance. Funding from Fund wallet..")
                    # initialise funder
                    funder = MonadSwapper(get_web3_connection(), FUNDER_PRIVATE_KEY)
                    funder.send_base_tokens(staker.wallet_address, FUND_AMT)
                else:
                    logging.error(f"Error {e}. Trying again..")
                    await asyncio.sleep(5)

        except Exception as e:
            color_print(f"An error occurred within the infinite loop\n{e}", "RED")
            color_print(f"Restarting Monad staker...", "MAGENTA")
            await asyncio.sleep(1 * 60 * 60)


async def ai_craft_voting(private_key):
    while True:  # Infinite loop, till you interrupt
        try:
            # Initialize the AiCraftFun class
            ai_craft = AiCraftFun(get_web3_connection(), private_key)

            try:
                # Sign in with a referral code
                ai_craft.sign_in(ref_code="ZFNMCQQDNC")

                project_id = "678376133438e102d6ff5c6e"  # for all voting regions
                # Display balances for a specific address
                ai_craft.display_wallet_balances()

                profile = ai_craft.get_user_info()
                remaining_voting = profile['data']['todayFeedCount']
                if remaining_voting >= 0:
                    for vote in range(remaining_voting):
                        logging.info(f"Account {ai_craft.display_address}: Prepping to vote..")
                        ai_craft.vote_by_country(
                            project_id=project_id,
                            ref_code="ZFNMCQQDNC",
                            country_code="NG"  # Nigeria
                        )
                        await timeout()  # Normal wait between swaps

                    logging.info(f"Account {ai_craft.display_address}: Voting complete.")
                    await timeout(60 * 60 * 24, 60 * 60 * 26)  # Long wait between cycles

            except Web3RPCError as e:
                if 'Signer had insufficient balance' in str(e):
                    logging.warning(
                     f"Account {ai_craft.display_address}: Signer had insufficient balance. Funding from Fund wallet..")
                    # initialise funder
                    funder = MonadSwapper(get_web3_connection(), FUNDER_PRIVATE_KEY)
                    funder.send_base_tokens(ai_craft.wallet_address, FUND_AMT)
                else:
                    logging.error(f"Error {e}. Trying again..")
                    await asyncio.sleep(5)

        except Exception as e:
            color_print(f"An error occurred within the infinite loop\n{e}", "RED")
            color_print(f"Restarting AI CRAFT...", "MAGENTA")
            await asyncio.sleep(1 * 60 * 60)


async def run_all(private_keys: list):
    tasks = []  # Collect all tasks here
    for private_key in private_keys:
        tasks.append(asyncio.gather(
            swap_tokens(private_key),
            stake_token(private_key),
            ai_craft_voting(private_key)
        ))

    # Run all tasks concurrently
    await asyncio.gather(*tasks)
