import random
import time
from colorama import init, Fore, Style
from utils import get_web3_connection, private_keys, data, handle_funding_error
import asyncio

# Initialize colorama
init(autoreset=True)

# Constants
RPC_URL = "https://testnet-rpc.monad.xyz/"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
WMON_CONTRACT = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"
CYCLES = data["DAILY_INTERACTION"]["DEX"]["bebop"]

# Smart contract ABI
contract_abi = [
    {"constant": False, "inputs": [], "name": "deposit", "outputs": [], "payable": True, "stateMutability": "payable",
     "type": "function"},
    {"constant": False, "inputs": [{"name": "amount", "type": "uint256"}], "name": "withdraw", "outputs": [],
     "payable": False, "stateMutability": "nonpayable", "type": "function"},
]


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


# Get web3 connection for account
def get_w3_for_account():
    try:
        return get_web3_connection()
    except Exception as e:
        print(f"{Fore.RED}❌ Web3 connection failed: {str(e)[:50]}...{Style.RESET_ALL}")
        return None


# Random delay (60-180 seconds)
def get_random_delay():
    return random.randint(60, 180)


# Wrap MON to WMON
def wrap_mon(private_key, amount, w3):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:5] + "..." + account.address[-5:]
        contract = w3.eth.contract(address=WMON_CONTRACT, abi=contract_abi)

        print_border(f"Wrap {w3.from_wei(amount, 'ether')} MON → WMON | {wallet}")
        tx = contract.functions.deposit().build_transaction({
            'from': account.address,
            'value': amount,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
        })

        estimated_gas = w3.eth.estimate_gas(tx)
        gas_with_buffer = int(estimated_gas * 1.1)
        tx['gas'] = gas_with_buffer

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
def unwrap_mon(private_key, amount, w3):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:5] + "..." + account.address[-5:]
        contract = w3.eth.contract(address=WMON_CONTRACT, abi=contract_abi)

        print_border(f"Unwrap {w3.from_wei(amount, 'ether')} WMON → MON | {wallet}")

        tx = contract.functions.withdraw(amount).build_transaction({
            'from': account.address,
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


def run_swap_cycle(cycles, private_keys):
    successful_accounts = 0

    for cycle in range(1, cycles + 1):
        for pk_idx, pk in enumerate(private_keys, 1):
            account_retries = 1

            while account_retries <= 3:
                try:
                    # Get fresh w3 connection for each account
                    w3 = get_w3_for_account()
                    if not w3:
                        raise Exception("Web3 connection failed")

                    wallet_ = w3.eth.account.from_key(pk).address
                    wallet = f"{wallet_[:5]}...{wallet_[-5:]}"

                    if account_retries == 1:
                        msg = f"CYCLE {cycle}/{cycles} | Account {pk_idx}: {wallet}"
                        print(f"{Fore.CYAN}{'═' * 60}{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}│ {msg:^56} │{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}{'═' * 60}{Style.RESET_ALL}")
                    else:
                        msg = f"CYCLE {cycle}/{cycles} | Account {pk_idx} RETRY {account_retries}/3: {wallet}"
                        print(f"{Fore.YELLOW}{'═' * 60}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}│ {msg:^56} │{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}{'═' * 60}{Style.RESET_ALL}")

                    amount = float(f"0.01{random.randint(1, 100)}")
                    amount_in_wei = w3.to_wei(amount, 'ether')
                    swap_retries = 1

                    while swap_retries <= 3:
                        try:
                            wrap_mon(pk, amount_in_wei, w3)
                            unwrap_mon(pk, amount_in_wei, w3)
                            break
                        except Exception as e:
                            print(f"{Fore.RED}⚠️ Swap attempt {swap_retries} failed: {str(e)[:50]}...{Style.RESET_ALL}")
                            if handle_funding_error(e, wallet_):
                                swap_retries += 1
                                continue
                            elif swap_retries < 3:
                                print(f"{Fore.YELLOW}🔄 Retrying swap in 30 seconds...{Style.RESET_ALL}")
                                time.sleep(30)
                                swap_retries += 1
                                continue
                            else:
                                raise  # Propagate error to account level

                    # If we reach here, account completed successfully
                    if cycle == 1:  # Count successful accounts on first cycle
                        successful_accounts += 1
                    print(f"{Fore.GREEN}✅ Account {pk_idx} cycle {cycle} completed successfully{Style.RESET_ALL}")
                    break  # Exit retry loop on success

                except Exception as e:
                    print(
                        f"{Fore.RED}❌ Account {pk_idx} attempt {account_retries} failed: {str(e)[:50]}...{Style.RESET_ALL}")

                    if handle_funding_error(e, wallet_ if 'wallet_' in locals() else 'Unknown'):
                        account_retries += 1
                        continue
                    elif account_retries < 3:
                        print(f"{Fore.YELLOW}🔄 Retrying account in 30 seconds...{Style.RESET_ALL}")
                        time.sleep(30)
                        account_retries += 1
                        continue
                    else:
                        print(f"{Fore.RED}💀 Account {pk_idx} failed after 3 attempts, skipping...{Style.RESET_ALL}")
                        break

            if cycle < cycles or pk != private_keys[-1]:
                delay = get_random_delay()
                print(f"\n{Fore.YELLOW}⏳ Waiting {delay} seconds...{Style.RESET_ALL}")
                time.sleep(delay)

    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(
        f"{Fore.GREEN}│ DONE: {cycles} cycles for {successful_accounts}/{len(private_keys)} accounts{' ' * (60 - 55 - len(str(cycles)) - len(str(successful_accounts)) - len(str(len(private_keys))))}│{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")


async def run():
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'BEBOP SWAP - MONAD TESTNET':^56} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

    if not private_keys:
        print(f"{Fore.RED}❌ pvkeys.txt not found{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}👥 Accounts: {len(private_keys)}{Style.RESET_ALL}")
    cycles = CYCLES

    print(f"{Fore.YELLOW}🚀 Running {cycles} swap cycles...{Style.RESET_ALL}")
    run_swap_cycle(cycles, private_keys)

    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'ALL DONE':^56} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")


if __name__ == "__main__":
    asyncio.run(run())