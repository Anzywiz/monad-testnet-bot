import logging
from eth_account import Account
from web3 import Web3
import colorlog
import json
import asyncio
import random
import requests
import os
from proxies import get_free_proxy


try:
    # Load data from the JSON file
    with open('config.json', "r") as file:
        data = json.load(file)
except FileNotFoundError:
    raise FileNotFoundError(f"config.json file does not exist. Create one")
except json.JSONDecodeError:
    raise ValueError(f"The config file is not a valid JSON file.")


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


RPC_URL = "https://testnet-rpc.monad.xyz"
FUNDER_PRIVATE_KEY = data["funder_private_key"]
FUND_AMT = 0.5


proxies = data["proxies"]
if proxies:
    print(f"Proxies found in config file")
else:
    print(f"Proxies NOT found in config file!")
    reply = input("Do you like to proceed with free proxies. Free proxies might be buggy (y/n): ")


def web3_proxy():
    if proxies:
        web3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"proxies": {'https': proxies, 'http': proxies}}))
    else:
        if reply.lower() == 'y':
            free_proxies = get_free_proxy()['proxy']
            web3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"proxies": free_proxies}))
        else:
            web3 = Web3(Web3.HTTPProvider(RPC_URL))
    return web3


class MonadSwapper:
    def __init__(self, your_private_key):
        """
        Initialize the MonadSwapper with blockchain connection details.

        Args:
            your_private_key (str): Private key of the wallet (without '0x' prefix)
        """

        self.web3 = web3_proxy()
        self.private_key = your_private_key
        self.account = Account.from_key(self.private_key)
        self.wallet_address = self.account.address
        self.no_0x_address = self.wallet_address.lower()[2:]
        self.contract_address = "0xC995498c22a012353FAE7eCC701810D673E25794"
        self.base_tx_data = {
            "chainId": 10143,
            "from": self.wallet_address,
            "gasPrice": self.web3.eth.gas_price,
            "to": self.contract_address,
        }
        # Contract addresses from the transaction (converted to checksum format)
        self.contract_address = self.to_checksum_address("0xC995498c22a012353FAE7eCC701810D673E25794")

    def short_address(self):
        address = f"{''.join(self.wallet_address[:5])}...{''.join(self.wallet_address[-4:])}"
        return address

    def get_bal(self):
        # get MON bal
        balance = self.web3.eth.get_balance(self.wallet_address)
        balance_eth = round(self.web3.from_wei(balance, 'ether'), 3)
        return balance_eth

    def to_checksum_address(self, address):
        """Convert address to checksum format."""
        return self.web3.to_checksum_address(address)

    def send_transaction(self, tx_data):

        logging.info(f'Account {self.short_address()}: Bal: {self.get_bal()} MON. Prepping to sign Tx...')
        # Sign the transaction
        signed_tx = self.web3.eth.account.sign_transaction(tx_data, self.private_key)
        # logging.info(f"Account {self.wallet_address}: Transaction signed!")

        # Send the transaction
        nonce = tx_data['nonce']
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logging.info(f"Account {self.short_address()}: Transaction #{nonce} sent. Hash: 0x{tx_hash.hex()}")
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_receipt

    def send_base_tokens(self, to_address, gwei_amount):
        # amount in wei
        amount = self.web3.to_wei(gwei_amount, 'ether')
        # Prepare transaction data
        tx_data = {
            'to': to_address,
            'value': amount,
            'gas': 21000,  # Standard gas limit for simple transfers
            'gasPrice': self.web3.eth.gas_price,
            'nonce': self.web3.eth.get_transaction_count(self.wallet_address),
            'chainId': self.web3.eth.chain_id
        }

        # Use our existing send_transaction method
        tx_receipt = self.send_transaction(tx_data)

        if tx_receipt.status == 1:
            logging.info(f"Account {self.short_address()}: Successfully sent {gwei_amount} MON to {to_address}")
        else:
            logging.error(f"Account {self.short_address()}: Token send failed!")

    def confirm_mon_swap(self, tx_data, amount_mon, token_symbol):

        tx_receipt = self.send_transaction(tx_data)

        if tx_receipt.status == 1:
            logging.info(f"Account {self.short_address()}: Successfully swapped {amount_mon} MON to {token_symbol}!")
        else:
            logging.error(f"Account {self.short_address()}: Transaction failed!")

    def swap_mon_to_chog(self, amount_mon):
        """
        Swap MON to CHOG tokens using copied input tx data.
        """
        input_data = "0x96f25cbe0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e0590015a873bf326bd645c3e1266d4db41c4e6b00000000000000000000000000000000000000000000000000005af3107a4000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001a0000000000000000000000000" + self.no_0x_address + '00000000000000000000000000000000000000000000000000156fca87b0713700000000000000000000000000000000000000000000000000000028861b00040000000000000000000000000000000000000000000000000000000000000004000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c5425701000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c5425701000000000000000000000000cba6b9a951749b8735c603e7ffc5151849248772000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c54257010000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000014000000000000000000000000000000000000000000000000000000000000002800000000000000000000000000000000000000000000000000000000000000004d0e30db0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000cba6b9a951749b8735c603e7ffc515184924877200000000000000000000000000000000000000000000000000005af3107a400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010438ed173900000000000000000000000000000000000000000000000000005af3107a400000000000000000000000000000000000000000000000000000156fca87b0713700000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000c995498c22a012353fae7ecc701810d673e2579400000000000000000000000000000000000000000000000000000028861b00040000000000000000000000000000000000000000000000000000000000000002000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c5425701000000000000000000000000e0590015a873bf326bd645c3e1266d4db41c4e6b000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000cba6b9a951749b8735c603e7ffc5151849248772000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',

        updated_data = {
            "data": input_data[0],
            "gas": 300000,
            "value": self.web3.to_wei(amount_mon, 'ether'),
            "nonce": self.web3.eth.get_transaction_count(self.wallet_address),
        }

        tx_data = {**self.base_tx_data, **updated_data}

        self.confirm_mon_swap(tx_data, amount_mon, 'CHOG')

    def swap_mon_to_dak(self, amount_mon, slippage_percent=0.5):
        """
        Swapping to DAK when considering slippage
        :param amount_mon:
        :param slippage_percent:
        :return:
        """

        input_data = "0x96f25cbe00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000f0bdebf0f83cd1ee3974779bcb7315f9808c71400000000000000000000000000000000000000000000000000038d7ea4c68000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001a0000000000000000000000000" + self.no_0x_address + "00000000000000000000000000000000000000000000000000561a5bf739b8c700000000000000000000000000000000000000000000000000000028864f492c0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c5425701000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c5425701000000000000000000000000d5abe08829813d5ae1a9b32c3b16a8fba07f9506000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c54257010000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000014000000000000000000000000000000000000000000000000000000000000002800000000000000000000000000000000000000000000000000000000000000004d0e30db0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000d5abe08829813d5ae1a9b32c3b16a8fba07f950600000000000000000000000000000000000000000000000000038d7ea4c6800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010438ed173900000000000000000000000000000000000000000000000000038d7ea4c6800000000000000000000000000000000000000000000000000000561a5bf739b8c700000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000c995498c22a012353fae7ecc701810d673e2579400000000000000000000000000000000000000000000000000000028864f492c0000000000000000000000000000000000000000000000000000000000000002000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c54257010000000000000000000000000f0bdebf0f83cd1ee3974779bcb7315f9808c714000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000d5abe08829813d5ae1a9b32c3b16a8fba07f9506000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        # Convert amount_mon to Wei
        amount_mon_wei = self.web3.to_wei(amount_mon, 'ether')

        # Extract the expected output amount from your input data
        # In your data, this appears to be: 0x000000000000000000000000000000000000000000000000561a5bf739b8c7
        expected_output_wei = int("0x561a5bf739b8c7", 16)

        # Calculate minimum output with slippage
        # If slippage is 0.5%, we want 99.5% of the expected output as minimum
        slippage_factor = 1 - (slippage_percent / 100)
        min_output_wei = int(expected_output_wei * slippage_factor)

        # Convert min_output_wei to hex string without '0x' prefix and padded to 64 characters
        min_output_hex = hex(min_output_wei)[2:].zfill(64)

        # Replace the expected output in your input data with the new minimum output
        # The expected output starts at position X in your input_data string
        # This is an approximate location - you'll need to verify the exact position
        position = input_data.find("0000000000000000000000000000000000000000000000000000561a5bf739b8c7")

        if position != -1:
            input_data = input_data[:position] + min_output_hex + input_data[position + 64:]

        updated_data = {
            "data": input_data,
            "gas": int("0x4407c", 16),
            "value": amount_mon_wei,
            "nonce": self.web3.eth.get_transaction_count(self.wallet_address),
        }

        tx_data = {**self.base_tx_data, **updated_data}
        self.confirm_mon_swap(tx_data, amount_mon, 'DAK')

    def swap_mon_to_yaki(self, amount_mon):

        input_data = "0x96f25cbe0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fe140e1dce99be9f4f15d657cd9b7bf622270c5000000000000000000000000000000000000000000000000000005af3107a4000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001a0000000000000000000000000" + self.no_0x_address + "000000000000000000000000000000000000000000000000013a8cf09fe3505f0000000000000000000000000000000000000000000000000000002886457cf80000000000000000000000000000000000000000000000000000000000000004000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c5425701000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c5425701000000000000000000000000cba6b9a951749b8735c603e7ffc5151849248772000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c54257010000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000014000000000000000000000000000000000000000000000000000000000000002800000000000000000000000000000000000000000000000000000000000000004d0e30db0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000cba6b9a951749b8735c603e7ffc515184924877200000000000000000000000000000000000000000000000000005af3107a400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010438ed173900000000000000000000000000000000000000000000000000005af3107a4000000000000000000000000000000000000000000000000000013a8cf09fe3505f00000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000c995498c22a012353fae7ecc701810d673e257940000000000000000000000000000000000000000000000000000002886457cf80000000000000000000000000000000000000000000000000000000000000002000000000000000000000000760afe86e5de5fa0ee542fc7b7b713e1c5425701000000000000000000000000fe140e1dce99be9f4f15d657cd9b7bf622270c50000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000cba6b9a951749b8735c603e7ffc5151849248772000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        updated_data = {
            "data": input_data,
            "gas": int("0x443c3", 16),
            "value": self.web3.to_wei(amount_mon, 'ether'),
            "nonce": self.web3.eth.get_transaction_count(self.wallet_address),

        }

        tx_data = {**self.base_tx_data, **updated_data}
        self.confirm_mon_swap(tx_data, amount_mon, 'YAKI')


async def timeout():
    timeout = random.randint(60, 100)
    logging.info(f"Awaiting {timeout}s timeout...")
    await asyncio.sleep(timeout)


async def swap_tokens(private_key, cycles=5):
    # Initialize the swapper
    swapper = MonadSwapper(private_key)
    count = 0
    while count < cycles:
        try:
            # Swap 0.0001 MON to CHOG
            swapper.swap_mon_to_chog(0.0001)
            await timeout()
            # swap to YAK
            swapper.swap_mon_to_yaki(0.0001)
            await timeout()
            count += 1
            logging.info(f"Account {swapper.short_address()}: Swap cycle count: {count}..")

        except Exception as e:
            if 'Signer had insufficient balance' in str(e):
                logging.warning(
                    f"Account {swapper.short_address()}: Signer had insufficient balance. Funding from Fund wallet..")
                # initialise funder
                funder = MonadSwapper(FUNDER_PRIVATE_KEY)
                FUND_AMT = 0.5
                funder.send_base_tokens(swapper.wallet_address, FUND_AMT)
            else:
                logging.error(f"Error {e}. Trying swap all over again..")

    logging.info(f"Account {swapper.short_address()}: Full Swap cycle complete.")
    await asyncio.sleep(60 * 60 * 12)


async def run_all(private_keys: list):
    tasks = []  # Collect all tasks here
    for private_key in private_keys:
        tasks.append(asyncio.gather(
            swap_tokens(private_key),
        ))

    # Run all tasks concurrently
    await asyncio.gather(*tasks)


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
        github_username = config.get('github_username')

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
                print(f"✅ Verified! {github_username} has starred {repo_url}")
                return True
            else:
                print(f"❌ Error: {github_username} has not starred {repo_url}")
                return False
        else:
            print(f"❌ Failed to retrieve stargazers. Status code: {response.status_code}")
            return False

    except requests.RequestException as e:
        print(f"Network error: {e}")
        return False
    except json.JSONDecodeError:
        print(f"❌ Error parsing config file at {config_path}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
