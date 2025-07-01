import random
import time
import asyncio
from colorama import init, Fore, Style
from utils import get_web3_connection, private_keys, data, handle_funding_error, monad_testnet_tokens

# Initialize colorama
init(autoreset=True)

# Constants
RPC_URL = "https://testnet-rpc.monad.xyz/"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
UNISWAP_V2_ROUTER_ADDRESS = "0xCa810D095e90Daae6e867c19DF6D9A8C56db2c89"
WETH_ADDRESS = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701"
CHAIN_ID = 10143  # Monad testnet chain ID
CYCLES = data["DAILY_INTERACTION"]["DEX"]["uniswap"]

# Token addresses
TOKEN_ADDRESSES = monad_testnet_tokens

# Contract ABIs
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf",
     "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}],
     "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
]

ROUTER_ABI = [
    {
        "name": "swapExactETHForTokens",
        "type": "function",
        "stateMutability": "payable",
        "inputs": [
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}]
    },
    {
        "name": "swapExactTokensForETH",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}]
    }
]


# Display functions
def print_border(text, color=Fore.CYAN, width=60):
    print(f"{color}┌{'─' * (width - 2)}┐{Style.RESET_ALL}")
    print(f"{color}│ {text:^56} │{Style.RESET_ALL}")
    print(f"{color}└{'─' * (width - 2)}┘{Style.RESET_ALL}")


def print_step(step, message):
    steps = {
        'approve': 'Approve Token',
        'swap_buy': 'Buy Token',
        'swap_sell': 'Sell Token',
        'balance': 'Balance Check'
    }
    step_text = steps.get(step, step.title())
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


# Random delay between 60-180 seconds
def get_random_delay():
    return random.randint(60, 180)


# Generate random amount (0.0001 - 0.01 MON)
def get_random_amount(w3):
    min_val = 0.0001
    max_val = 0.01
    random_amount = random.uniform(min_val, max_val)
    return w3.to_wei(round(random_amount, 6), 'ether')


# Approve token spending
async def approve_token(private_key, token_address, amount, token_symbol, w3):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:5] + "..." + account.address[-5:]

        token_contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
        balance = token_contract.functions.balanceOf(account.address).call()

        if balance < amount:
            raise ValueError(
                f"Insufficient {token_symbol} balance: {w3.from_wei(balance, 'ether')} < {w3.from_wei(amount, 'ether')}")

        print_step('approve', f'Approving {token_symbol} spending')

        tx = token_contract.functions.approve(w3.to_checksum_address(UNISWAP_V2_ROUTER_ADDRESS),
                                              amount).build_transaction({
            'from': account.address,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': CHAIN_ID
        })

        estimated_gas = w3.eth.estimate_gas(tx)
        tx['gas'] = estimated_gas

        gas_price_wei = w3.eth.gas_price
        gas_cost_wei = estimated_gas * gas_price_wei
        gas_cost_mon = w3.from_wei(gas_cost_wei, 'ether')

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print_step('approve',
                   f"Tx: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL} | Gas {gas_cost_mon} MON")
        await asyncio.sleep(1)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt['status'] != 1:
            raise Exception(f"Approval failed: Status {receipt['status']}")

        print_step('approve', f"{Fore.GREEN}Approval successful!{Style.RESET_ALL}")

    except Exception as e:
        print_step('approve', f"{Fore.RED}Failed: {str(e)}{Style.RESET_ALL}")
        raise


# Swap MON to token
async def swap_mon_to_token(private_key, token_address, amount, token_symbol, w3):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:5] + "..." + account.address[-5:]

        start_msg = f"Buy {w3.from_wei(amount, 'ether')} MON → {token_symbol} | {wallet}"
        print_border(start_msg)

        mon_balance = w3.eth.get_balance(account.address)
        if mon_balance < amount:
            raise ValueError(
                f"Insufficient MON balance: {w3.from_wei(mon_balance, 'ether')} < {w3.from_wei(amount, 'ether')}")

        router_contract = w3.eth.contract(address=w3.to_checksum_address(UNISWAP_V2_ROUTER_ADDRESS), abi=ROUTER_ABI)

        tx = router_contract.functions.swapExactETHForTokens(
            0,  # amountOutMin (0 for simplicity)
            [w3.to_checksum_address(WETH_ADDRESS), w3.to_checksum_address(token_address)],
            account.address,
            int(time.time()) + 600  # deadline
        ).build_transaction({
            'from': account.address,
            'value': amount,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': CHAIN_ID
        })

        estimated_gas = w3.eth.estimate_gas(tx)
        tx['gas'] = estimated_gas

        gas_price_wei = w3.eth.gas_price
        gas_cost_wei = estimated_gas * gas_price_wei
        gas_cost_mon = w3.from_wei(gas_cost_wei, 'ether')

        print_step('swap_buy', 'Sending transaction...')
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print_step('swap_buy',
                   f"Tx: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL} | Gas {gas_cost_mon} MON")
        await asyncio.sleep(1)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt['status'] == 1:
            print_step('swap_buy', f"{Fore.GREEN}Buy successful!{Style.RESET_ALL}")
        else:
            raise Exception(f"Transaction failed: Status {receipt['status']}")

    except Exception as e:
        print_step('swap_buy', f"{Fore.RED}Failed: {str(e)}{Style.RESET_ALL}")
        raise


# Swap token to MON
async def swap_token_to_mon(private_key, token_address, token_symbol, w3):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:5] + "..." + account.address[-5:]

        start_msg = f"Sell {token_symbol} → MON | {wallet}"
        print_border(start_msg)

        token_contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
        balance = token_contract.functions.balanceOf(account.address).call()

        if balance == 0:
            print_step('swap_sell', f"{Fore.YELLOW}No {token_symbol} balance, skipping{Style.RESET_ALL}")
            return

        # Approve token spending
        await approve_token(private_key, token_address, balance, token_symbol, w3)

        router_contract = w3.eth.contract(address=w3.to_checksum_address(UNISWAP_V2_ROUTER_ADDRESS), abi=ROUTER_ABI)

        tx = router_contract.functions.swapExactTokensForETH(
            balance,  # amountIn
            0,  # amountOutMin (0 for simplicity)
            [w3.to_checksum_address(token_address), w3.to_checksum_address(WETH_ADDRESS)],
            account.address,
            int(time.time()) + 600  # deadline
        ).build_transaction({
            'from': account.address,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': CHAIN_ID
        })

        estimated_gas = w3.eth.estimate_gas(tx)
        tx['gas'] = estimated_gas

        gas_price_wei = w3.eth.gas_price
        gas_cost_wei = estimated_gas * gas_price_wei
        gas_cost_mon = w3.from_wei(gas_cost_wei, 'ether')

        print_step('swap_sell', 'Sending transaction...')
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print_step('swap_sell',
                   f"Tx: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL} | Gas {gas_cost_mon} MON")
        await asyncio.sleep(1)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt['status'] == 1:
            print_step('swap_sell', f"{Fore.GREEN}Sell successful!{Style.RESET_ALL}")
        else:
            raise Exception(f"Transaction failed: Status {receipt['status']}")

    except Exception as e:
        print_step('swap_sell', f"{Fore.RED}Failed: {str(e)}{Style.RESET_ALL}")
        raise


# Run swap cycle for each private key
async def run_swap_cycle(cycles, private_keys):
    successful_accounts = 0

    for account_idx, private_key in enumerate(private_keys, 1):
        account_retries = 1

        while account_retries <= 3:
            try:
                # Get fresh w3 connection for each account attempt
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
                    print_border(f"UNISWAP CYCLE {i + 1}/{cycles} | {wallet}")
                    amount = get_random_amount(w3)

                    # Randomly select a token to trade
                    token_symbol, token_address = random.choice(list(TOKEN_ADDRESSES.items()))
                    swap_retries = 1

                    while swap_retries <= 3:
                        try:
                            # Buy token with MON
                            await swap_mon_to_token(private_key, token_address, amount, token_symbol, w3)
                            await asyncio.sleep(random.randint(30, 60))  # Wait between swaps

                            # Sell token back to MON
                            # await swap_token_to_mon(private_key, token_address, token_symbol, w3)
                            break

                        except Exception as e:
                            print(f"{Fore.RED}⚠️ Swap attempt {swap_retries} failed: {str(e)[:50]}...{Style.RESET_ALL}")
                            if handle_funding_error(e, wallet_):
                                swap_retries += 1
                                continue
                            elif swap_retries < 3:
                                print(f"{Fore.YELLOW}🔄 Retrying swap in 30 seconds...{Style.RESET_ALL}")
                                await asyncio.sleep(30)
                                # Randomly select a token to trade
                                token_symbol, token_address = random.choice(list(TOKEN_ADDRESSES.items()))
                                swap_retries += 1
                                continue
                            else:
                                raise  # Propagate error to account level

                    if i < cycles - 1:
                        delay = random.randint(30, 60)
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
    print(f"{Fore.GREEN}│ {'UNISWAP V2 - MONAD TESTNET':^56} │{Style.RESET_ALL}")
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