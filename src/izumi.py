import random
import asyncio
from utils import get_web3_connection, private_keys, data, handle_funding_error
from colorama import init, Fore, Style
import time

# Initialize colorama
init(autoreset=True)

# Constants
RPC_URL = "https://testnet-rpc.monad.xyz/"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
WMON_CONTRACT = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"
CYCLES = data["DAILY_INTERACTION"]["DEX"]["izumi"]

# Smart contract ABI
contract_abi = [
    {"constant": False, "inputs": [], "name": "deposit", "outputs": [], "payable": True, "stateMutability": "payable",
     "type": "function"},
    {"constant": False, "inputs": [{"name": "amount", "type": "uint256"}], "name": "withdraw", "outputs": [],
     "payable": False, "stateMutability": "nonpayable", "type": "function"},
]


# Print border function
def print_border(text, color=Fore.CYAN, width=60):
    print(f"{color}┌{'─' * (width - 2)}┐{Style.RESET_ALL}")
    print(f"{color}│ {text:^56} │{Style.RESET_ALL}")
    print(f"{color}└{'─' * (width - 2)}┘{Style.RESET_ALL}")


# Print step function
def print_step(step, message):
    step_text = "Wrap MON" if step == 'wrap' else "Unwrap WMON"
    print(f"{Fore.YELLOW}➤ {Fore.CYAN}{step_text:<15}{Style.RESET_ALL} | {message}")


# Get web3 connection for account
def get_w3_for_account():
    try:
        w3 = get_web3_connection()
        if not w3.is_connected():
            raise Exception("RPC connection failed")
        return w3
    except Exception as e:
        print(f"{Fore.RED}❌ Web3 connection failed: {str(e)[:50]}...{Style.RESET_ALL}")
        return None


# Generate random amount (0.01 - 0.05 MON)
def get_random_amount(w3):
    min_val = 0.01
    max_val = 0.05
    random_amount = random.uniform(min_val, max_val)
    return w3.to_wei(round(random_amount, 4), 'ether')


# Generate random delay (1-3 minutes)
def get_random_delay():
    return random.randint(60, 180)  # Returns seconds


# Wrap MON to WMON
async def wrap_mon(private_key, amount, w3):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:5] + "..." + account.address[-5:]
        contract = w3.eth.contract(address=WMON_CONTRACT, abi=contract_abi)

        print_border(f"Wrapping {w3.from_wei(amount, 'ether')} MON → WMON | {wallet}")
        tx = contract.functions.deposit().build_transaction({
            'from': account.address,
            'value': amount,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
        })

        estimated_gas = w3.eth.estimate_gas(tx)
        tx['gas'] = estimated_gas

        gas_price_wei = w3.eth.gas_price
        gas_cost_wei = estimated_gas * gas_price_wei
        gas_cost_mon = w3.from_wei(gas_cost_wei, 'ether')

        print_step('wrap', 'Sending transaction...')
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print_step('wrap', f"Tx: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL} | Gas {gas_cost_mon} MON")
        await asyncio.sleep(1)
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print_step('wrap', f"{Fore.GREEN}Wrap successful!{Style.RESET_ALL}")

    except Exception as e:
        print_step('wrap', f"{Fore.RED}Failed: {str(e)}{Style.RESET_ALL}")
        raise


# Unwrap WMON to MON
async def unwrap_mon(private_key, amount, w3):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:5] + "..." + account.address[-5:]
        contract = w3.eth.contract(address=WMON_CONTRACT, abi=contract_abi)

        print_border(f"Unwrapping {w3.from_wei(amount, 'ether')} WMON → MON | {wallet}")
        tx = contract.functions.withdraw(amount).build_transaction({
            'from': account.address,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
        })

        estimated_gas = w3.eth.estimate_gas(tx)
        tx['gas'] = estimated_gas

        gas_price_wei = w3.eth.gas_price
        gas_cost_wei = estimated_gas * gas_price_wei
        gas_cost_mon = w3.from_wei(gas_cost_wei, 'ether')

        print_step('unwrap', 'Sending transaction...')
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print_step('unwrap',
                   f"Tx: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}. | Gas {gas_cost_mon} MON")
        await asyncio.sleep(1)
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print_step('unwrap', f"{Fore.GREEN}Unwrap successful!{Style.RESET_ALL}")

    except Exception as e:
        print_step('unwrap', f"{Fore.RED}Failed: {str(e)}{Style.RESET_ALL}")
        raise


# Run swap cycle for each private key
async def run_swap_cycle(cycles, private_keys):
    successful_accounts = 0

    for account_idx, private_key in enumerate(private_keys, 1):
        account_retries = 1

        while account_retries <= 3:
            try:
                # Get fresh w3 connection for each account
                w3 = get_w3_for_account()
                if not w3:
                    raise Exception("Web3 connection failed")

                wallet_ = w3.eth.account.from_key(private_key).address
                wallet = f"{wallet_[:5]}...{wallet_[-5:]}"

                if account_retries == 1:
                    print_border(f"ACCOUNT {account_idx}/{len(private_keys)} | {wallet}", Fore.CYAN)
                else:
                    print_border(f"ACCOUNT {account_idx}/{len(private_keys)} RETRY {account_retries}/3 | {wallet}",
                                 Fore.YELLOW)

                for i in range(cycles):
                    print_border(f"SWAP CYCLE {i + 1}/{cycles} | {wallet}")
                    amount = get_random_amount(w3)
                    swap_retries = 1

                    while swap_retries <= 3:
                        try:
                            await wrap_mon(private_key, amount, w3)
                            await unwrap_mon(private_key, amount, w3)
                            break
                        except Exception as e:
                            print(f"{Fore.RED}⚠️ Swap attempt {swap_retries} failed: {str(e)[:50]}...{Style.RESET_ALL}")
                            if handle_funding_error(e, wallet_):
                                swap_retries += 1
                                continue
                            elif swap_retries < 3:
                                print(f"{Fore.YELLOW}🔄 Retrying swap in 30 seconds...{Style.RESET_ALL}")
                                await asyncio.sleep(30)
                                swap_retries += 1
                                continue
                            else:
                                raise  # Propagate error to account level

                    if i < cycles - 1:
                        delay = get_random_delay()
                        print(
                            f"\n{Fore.YELLOW}⏳ Waiting {delay / 60:.1f} minutes before next cycle...{Style.RESET_ALL}")
                        await asyncio.sleep(delay)

                # If we reach here, all cycles completed successfully
                successful_accounts += 1
                print(f"{Fore.GREEN}✅ Account {account_idx} completed successfully{Style.RESET_ALL}")
                break  # Exit retry loop on success

            except Exception as e:
                print(
                    f"{Fore.RED}❌ Account {account_idx} attempt {account_retries} failed: {str(e)[:50]}...{Style.RESET_ALL}")

                if handle_funding_error(e, wallet_ if 'wallet_' in locals() else 'Unknown'):
                    account_retries += 1
                    continue
                elif account_retries < 3:
                    print(f"{Fore.YELLOW}🔄 Retrying account in 30 seconds...{Style.RESET_ALL}")
                    await asyncio.sleep(30)
                    account_retries += 1
                    continue
                else:
                    print(f"{Fore.RED}💀 Account {account_idx} failed after 3 attempts, skipping...{Style.RESET_ALL}")
                    break

        if account_idx < len(private_keys):
            delay = get_random_delay()
            print(f"\n{Fore.YELLOW}⏳ Waiting {delay / 60:.1f} minutes before next account...{Style.RESET_ALL}")
            await asyncio.sleep(delay)

    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(
        f"{Fore.GREEN}│ DONE: {successful_accounts}/{len(private_keys)} accounts, {cycles} cycles each{' ' * (60 - 55 - len(str(successful_accounts)) - len(str(len(private_keys))) - len(str(cycles)))}│{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")


# Main function
async def run():
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'IZUMI SWAP - MONAD TESTNET':^56} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

    if not private_keys:
        print(f"{Fore.RED}❌ No private keys found{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}👥 Accounts: {len(private_keys)}{Style.RESET_ALL}")
    cycles = CYCLES

    print(f"{Fore.YELLOW}🚀 Running {cycles} swap cycles for {len(private_keys)} accounts...{Style.RESET_ALL}")
    await run_swap_cycle(cycles, private_keys)


if __name__ == "__main__":
    asyncio.run(run())