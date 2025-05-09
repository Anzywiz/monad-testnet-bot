import random
import time
from colorama import init, Fore, Style
from utils import get_web3_connection, private_keys, data

# Initialize colorama
init(autoreset=True)

# Constants
RPC_URL = "https://testnet-rpc.monad.xyz/"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
WMON_CONTRACT = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"
CYCLES = data["DAILY_INTERACTION"]["DEX"]["bebop"]


# Display border function
def print_border(text, color=Fore.CYAN, width=60):
    print(f"{color}┌{'─' * (width - 2)}┐{Style.RESET_ALL}")
    print(f"{color}│ {text:^19} │{Style.RESET_ALL}")
    print(f"{color}└{'─' * (width - 2)}┘{Style.RESET_ALL}")


# Display step function
def print_step(step, message):
    steps = {
        'wrap': 'Wrap MON',
        'unwrap': 'Unwrap WMON'
    }
    step_text = steps[step]
    print(f"{Fore.YELLOW}➤ {Fore.CYAN}{step_text:<15}{Style.RESET_ALL} | {message}")


# Load private keys from prkeys.txt
def load_private_keys(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"{Fore.RED}❌ Error reading file: {str(e)}{Style.RESET_ALL}")
        return None


# Initialize web3 provider
w3 = get_web3_connection()

# Smart contract ABI
contract_abi = [
    {"constant": False, "inputs": [], "name": "deposit", "outputs": [], "payable": True, "stateMutability": "payable",
     "type": "function"},
    {"constant": False, "inputs": [{"name": "amount", "type": "uint256"}], "name": "withdraw", "outputs": [],
     "payable": False, "stateMutability": "nonpayable", "type": "function"},
]

# Initialize contract
contract = w3.eth.contract(address=WMON_CONTRACT, abi=contract_abi)


# Get MON amount from user
def get_mon_amount_from_user():
    while True:
        try:
            print_border("Enter MON amount (0.01 - 999)", Fore.YELLOW)
            amount = float(input(f"{Fore.GREEN}➤ {Style.RESET_ALL}"))
            if 0.01 <= amount <= 999:
                return w3.to_wei(amount, 'ether')
            print(f"{Fore.RED}❌ Amount must be 0.01-999 / Enter a valid number!{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}❌ Amount must be 0.01-999 / Enter a valid number!{Style.RESET_ALL}")


# Random delay (60-180 seconds)
def get_random_delay():
    return random.randint(60, 180)


# Wrap MON to WMON
def wrap_mon(private_key, amount):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:5] + "..." + account.address[-5:]

        print_border(f"Wrap {w3.from_wei(amount, 'ether')} MON → WMON | {wallet}")
        tx = contract.functions.deposit().build_transaction({
            'from': account.address,
            'value': amount,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
        })

        # Estimate the gas required for this transaction
        estimated_gas = w3.eth.estimate_gas(tx)

        # Add some buffer (e.g., 20%) to ensure the transaction has enough gas
        gas_with_buffer = int(estimated_gas * 1.1)

        # Update the transaction with the estimated gas
        tx['gas'] = gas_with_buffer
        # Calculate the gas cost in the native token (MON)
        gas_price_wei = w3.eth.gas_price
        gas_cost_wei = gas_with_buffer * gas_price_wei
        gas_cost_mon = w3.from_wei(gas_cost_wei, 'ether')

        print_step('wrap', 'Sending transaction...')
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print_step('wrap', f"Gas {gas_cost_mon} MON. Tx: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}")
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print_step('wrap', f"{Fore.GREEN}Wrap successful!{Style.RESET_ALL}")

    except Exception as e:
        print_step('wrap', f"{Fore.RED}Failed: {str(e)}{Style.RESET_ALL}")
        raise


# Unwrap WMON to MON
def unwrap_mon(private_key, amount):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:5] + "..." + account.address[-5:]

        print_border(f"Unwrap {w3.from_wei(amount, 'ether')} WMON → MON | {wallet}")

        tx = contract.functions.withdraw(amount).build_transaction({
            'from': account.address,
            # 'gas': 500000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
        })

        estimated_gas = w3.eth.estimate_gas(tx)
        tx['gas'] = estimated_gas

        gas_cost_mon = w3.from_wei(w3.eth.gas_price * estimated_gas, 'ether')

        print_step('unwrap', f'Gas {gas_cost_mon} MON. | Sending transaction...')
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print_step('unwrap', f"Tx: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}")
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print_step('unwrap', f"{Fore.GREEN}Unwrap successful!{Style.RESET_ALL}")

    except Exception as e:
        print_step('unwrap', f"{Fore.RED}Failed: {str(e)}{Style.RESET_ALL}")
        raise


# Run swap cycle
def run_swap_cycle(cycles, private_keys):
    for cycle in range(1, cycles + 1):
        for pk in private_keys:
            wallet_ = w3.eth.account.from_key(pk).address
            wallet = f"{wallet_[:5]}...{wallet_[-5:]}"
            msg = f"CYCLE {cycle}/{cycles} | Account: {wallet}"
            print(f"{Fore.CYAN}{'═' * 60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│ {msg:^56} │{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'═' * 60}{Style.RESET_ALL}")

            amount = float(f"0.01{random.randint(1, 100)}")
            amount_in_wei = w3.to_wei(amount, 'ether')
            wrap_mon(pk, amount_in_wei)
            unwrap_mon(pk, amount_in_wei)

            if cycle < cycles or pk != private_keys[-1]:
                delay = get_random_delay()
                print(f"\n{Fore.YELLOW}⏳ Waiting {delay} seconds...{Style.RESET_ALL}")
                time.sleep(delay)


async def run():
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'BEBOP SWAP - MONAD TESTNET':^56} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

    # Load private keys
    if not private_keys:
        print(f"{Fore.RED}❌ pvkeys.txt not found{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}👥 Accounts: {len(private_keys)}{Style.RESET_ALL}")

    cycles = CYCLES

    # Run script
    print(f"{Fore.YELLOW}🚀 Running {cycles} swap cycles...{Style.RESET_ALL}")
    run_swap_cycle(cycles, private_keys)

    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'ALL DONE':^19} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")


if __name__ == "__main__":
    run()
