import random
import asyncio
import time
from colorama import init, Fore, Style
from utils import get_web3_connection, private_keys, data, handle_funding_error

# Initialize colorama
init(autoreset=True)

# Constants
CYCLES = data["DAILY_INTERACTION"]["DEX"]["bean"]

EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
ROUTER_ADDRESS = "0xCa810D095e90Daae6e867c19DF6D9A8C56db2c89"
WMON_ADDRESS = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"

# List of supported tokens
TOKENS = {
    "USDC": {
        "address": "0xf817257fed379853cDe0fa4F97AB987181B1E5Ea",
        "symbol": "USDC",
        "name": "USD Coin",
        "minAmount": 0.01,
        "maxAmount": 1,
        "decimals": 6,
    },
    "USDT": {
        "address": "0x88b8E2161DEDC77EF4ab7585569D2415a1C1055D",
        "symbol": "USDT",
        "name": "Tether USD",
        "minAmount": 0.01,
        "maxAmount": 1,
        "decimals": 6,
    },
    "BEAN": {
        "address": "0x268E4E24E0051EC27b3D27A95977E71cE6875a05",
        "symbol": "BEAN",
        "name": "Bean Token",
        "minAmount": 0.01,
        "maxAmount": 1,
        "decimals": 6,
    },
    "JAI": {
        "address": "0x70F893f65E3C1d7f82aad72f71615eb220b74D10",
        "symbol": "JAI",
        "name": "Jai Token",
        "minAmount": 0.01,
        "maxAmount": 1,
        "decimals": 6,
    },
}

# ABI for ERC20 token
ERC20_ABI = [
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf",
     "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}
]

# ABI for router
ROUTER_ABI = [
    {"inputs": [{"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "swapExactETHForTokens",
     "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}], "stateMutability": "payable",
     "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "swapExactTokensForETH",
     "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
     "stateMutability": "nonpayable", "type": "function"}
]


# Function to read private keys from private_keys.txt
def load_private_keys(file_path):
    try:
        with open(file_path, 'r') as file:
            keys = [line.strip() for line in file.readlines() if line.strip()]
            if not keys:
                raise ValueError("private_keys.txt is empty")
            return keys
    except FileNotFoundError:
        print(f"{Fore.RED}❌ private_keys.txt not found{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}❌ Error reading private_keys.txt: {str(e)}{Style.RESET_ALL}")
        return None


# Function to display pretty border
def print_border(text, color=Fore.MAGENTA, width=60):
    print(f"{color}╔{'═' * (width - 2)}╗{Style.RESET_ALL}")
    print(f"{color}║ {text:^56} ║{Style.RESET_ALL}")
    print(f"{color}╚{'═' * (width - 2)}╝{Style.RESET_ALL}")


# Function to display step
def print_step(step, message):
    steps = {'approve': 'Approve Token', 'swap': 'Swap'}
    step_text = steps[step]
    print(f"{Fore.YELLOW}🔸 {Fore.CYAN}{step_text:<15}{Style.RESET_ALL} | {message}")


# Generate random amount (0.001 - 0.01 MON)
def get_random_amount():
    return round(random.uniform(0.001, 0.01), 6)


# Generate random delay (1-3 minutes)
def get_random_delay():
    return random.randint(60, 180)  # Returns seconds


# Function to approve token with retry
async def approve_token(w3, private_key, token_address, amount, decimals, max_retries=3):
    for attempt in range(max_retries):
        try:
            account = w3.eth.account.from_key(private_key)
            wallet = account.address[:5] + "..." + account.address[-5:]
            token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
            symbol = token_contract.functions.symbol().call()

            print_step('approve', f'Checking approval for {symbol}')
            amount_in_decimals = w3.to_wei(amount, 'ether') if decimals == 18 else int(amount * 10 ** decimals)
            tx = token_contract.functions.approve(ROUTER_ADDRESS, amount_in_decimals).build_transaction({
                'from': account.address,
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(account.address),
            })

            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            await asyncio.sleep(2)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            if receipt.status == 1:
                print_step('approve', f"{Fore.GREEN}✔ {symbol} approved{Style.RESET_ALL}")
                return amount_in_decimals
            else:
                raise Exception(f"Approve failed: Status {receipt.status}")
        except Exception as e:
            if "429 Client Error" in str(e) and attempt < max_retries - 1:
                delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print_step('approve', f"{Fore.YELLOW}Rate limited, retrying in {delay} seconds...{Style.RESET_ALL}")
                await asyncio.sleep(delay)
            else:
                print_step('approve', f"{Fore.RED}✘ Failed: {str(e)}{Style.RESET_ALL}")
                raise


# Function to swap Token to MON
async def swap_token_to_mon(w3, private_key, token_symbol, amount):
    token = TOKENS[token_symbol]
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:5] + "..." + account.address[-5:]

        print_border(f"Swap {amount} {token_symbol} to MON | {wallet}", Fore.MAGENTA)

        amount_in_decimals = await approve_token(w3, private_key, token['address'], amount, token['decimals'])

        router = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI)
        tx = router.functions.swapExactTokensForETH(
            amount_in_decimals, 0, [token['address'], WMON_ADDRESS], account.address, int(time.time()) + 600
        ).build_transaction({
            'from': account.address,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
        })

        estimated_gas = w3.eth.estimate_gas(tx)
        tx['gas'] = estimated_gas

        print_step('swap', 'Sending swap transaction...')
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print_step('swap', f"Tx Hash: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}")
        await asyncio.sleep(2)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

        if receipt.status == 1:
            print_step('swap', f"{Fore.GREEN}✔ Swap successful!{Style.RESET_ALL}")
            return True
        else:
            raise Exception(f"Transaction failed: Status {receipt.status}")
    except Exception as e:
        print_step('swap', f"{Fore.RED}✘ Failed: {str(e)}{Style.RESET_ALL}")
        raise e


# Function to swap MON to Token
async def swap_mon_to_token(w3, private_key, token_symbol, amount):
    token = TOKENS[token_symbol]
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:5] + "..." + account.address[-5:]

        print_border(f"Swap {amount} MON to {token_symbol} | {wallet}", Fore.MAGENTA)

        tx = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI).functions.swapExactETHForTokens(
            0, [WMON_ADDRESS, token['address']], account.address, int(time.time()) + 600
        ).build_transaction({
            'from': account.address,
            'value': w3.to_wei(amount, 'ether'),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
        })

        print_step('swap', 'Sending swap transaction...')
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print_step('swap', f"Tx Hash: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}")
        await asyncio.sleep(2)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

        if receipt.status == 1:
            print_step('swap', f"{Fore.GREEN}✔ Swap successful!{Style.RESET_ALL}")
            return True
        else:
            raise Exception(f"Transaction failed: Status {receipt.status}")
    except Exception as e:
        print_step('swap', f"{Fore.RED}✘ Failed: {str(e)}{Style.RESET_ALL}")
        raise e


# Function to check balance with retry
async def check_balance(w3, private_key, max_retries=3):
    account = w3.eth.account.from_key(private_key)
    wallet = account.address[:5] + "..." + account.address[-5:]
    print_border(f"💰 Balance | {wallet}", Fore.CYAN)

    try:
        mon_balance = w3.eth.get_balance(account.address)
        print_step('swap', f"MON: {Fore.CYAN}{w3.from_wei(mon_balance, 'ether')}{Style.RESET_ALL}")
    except Exception as e:
        print_step('swap', f"MON: {Fore.RED}Error reading balance - {str(e)}{Style.RESET_ALL}")

    for symbol, token in TOKENS.items():
        for attempt in range(max_retries):
            try:
                token_contract = w3.eth.contract(address=token['address'], abi=ERC20_ABI)
                balance = token_contract.functions.balanceOf(account.address).call()
                print_step('swap', f"{symbol}: {Fore.CYAN}{balance / 10 ** token['decimals']}{Style.RESET_ALL}")
                break
            except Exception as e:
                if "429 Client Error" in str(e) and attempt < max_retries - 1:
                    delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print_step('swap',
                               f"{Fore.YELLOW}{symbol}: Rate limited, retrying in {delay} seconds...{Style.RESET_ALL}")
                    await asyncio.sleep(delay)
                else:
                    print_step('swap', f"{symbol}: {Fore.RED}Error reading balance - {str(e)}{Style.RESET_ALL}")
                    break
            await asyncio.sleep(1)  # Delay between tokens


# Function to perform random swap
async def perform_random_swap(w3, private_key):
    account = w3.eth.account.from_key(private_key)
    wallet = account.address[:5] + "..." + account.address[-5:]
    is_mon_to_token = True
    token_symbols = list(TOKENS.keys())
    token_symbol = random.choice(token_symbols)
    token = TOKENS[token_symbol]

    if is_mon_to_token:
        amount = get_random_amount()
        amount_in_wei = w3.to_wei(amount, 'ether')
        print_border(f"🎲 Random Swap: {amount} MON → {token_symbol} | {wallet}", Fore.YELLOW)
        return await swap_mon_to_token(w3, private_key, token_symbol, amount)
    else:
        amount = get_random_amount()
        print_border(f"🎲 Random Swap: {amount} {token_symbol} → MON | {wallet}", Fore.YELLOW)
        return await swap_token_to_mon(w3, private_key, token_symbol, amount)


# Run swap cycle
async def run_swap_cycle(cycles, private_keys):
    successful_accounts = 0

    for account_idx, private_key in enumerate(private_keys, 1):
        account_retries = 1

        while account_retries <= 3:
            try:
                # Initialize web3 provider
                w3 = get_web3_connection()
                account = w3.eth.account.from_key(private_key)
                wallet = account.address[:5] + "..." + account.address[-5:]

                if account_retries == 1:
                    print_border(f"🏦 ACCOUNT {account_idx}/{len(private_keys)} | {wallet}", Fore.BLUE)
                else:
                    print_border(f"🏦 ACCOUNT {account_idx}/{len(private_keys)} RETRY {account_retries}/3 | {wallet}",
                                 Fore.YELLOW)

                await check_balance(w3, private_key)

                for i in range(cycles):
                    print_border(f"🔄 BEAN SWAP CYCLE {i + 1}/{cycles} | {wallet}", Fore.CYAN)
                    retries = 1
                    while retries <= 3:
                        try:
                            success = await perform_random_swap(w3, private_key)
                            if success:
                                await check_balance(w3, private_key)
                                break
                        except Exception as e:
                            if handle_funding_error(e, account.address):
                                time.sleep(30)
                                retries += 1
                                continue
                            else:
                                raise e

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

                if handle_funding_error(e, account.address if 'account' in locals() else 'Unknown'):
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
        f"{Fore.GREEN}│ DONE: {successful_accounts}/{len(private_keys)} accounts, {cycles} cycles each{' ' * (60 - 50 - len(str(successful_accounts)) - len(str(len(private_keys))) - len(str(cycles)))}│{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")


# Main function
async def run():
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'BEAN SWAP - MONAD TESTNET':^56} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

    print(f"{Fore.CYAN}👥 Accounts: {len(private_keys)}{Style.RESET_ALL}")

    await run_swap_cycle(CYCLES, private_keys)


if __name__ == "__main__":
    asyncio.run(run())
