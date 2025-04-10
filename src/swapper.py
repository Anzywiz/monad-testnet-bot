import requests
from web3 import Web3
from typing import Dict, Any, Optional, List
from src.logger import color_print
import logging
import time
from src.proxies import get_phantom_headers


class MonadSwapper:
    """
    A client for performing token swaps on Monad network using Monorail pathfinder API.
    """

    # Token address constants
    TOKENS = {
        "MON": "0x0000000000000000000000000000000000000000",  # Native token
        "WMON": "0x760afe86e5de5fa0ee542fc7b7b713e1c5425701",
        "CHOG": "0xe0590015a873bf326bd645c3e1266d4db41c4e6b",
        "DAK": "0x0f0bdebf0f83cd1ee3974779bcb7315f9808c714",
        "YAKI": "0xfe140e1dce99be9f4f15d657cd9b7bf622270c50",
        "USDC": "0x5d876d73f4441d5f2438b1a3e2a51771b337f27a",  # Updated from the JSON
        "sMON": "0x07aabd925866e8353407e67c1d157836f7ad923e"
    }

    # Base URLs for Monorail APIs
    BASE_URL = "https://testnet-pathfinder-v2.monorail.xyz/v1/quote"
    BALANCE_URL = "https://testnet-api.monorail.xyz/v1/wallet/{address}/balances"

    def __init__(self, w3: Web3, private_key: Optional[str] = None, rpc_url: str = "https://testnet-rpc.monad.xyz") -> None:
        """
        Initialize the MonadSwapper with optional Web3 connection details.

        Args:
            private_key: Optional private key for signing transactions
            rpc_url: RPC URL for the Monad network
        """
        self.w3 = w3
        if not self.w3.is_connected():
            raise Exception("Failed to connect to Monad network")

        self.private_key = private_key

        if private_key:
            self.account = self.w3.eth.account.from_key(private_key)
            self.wallet_address = self.account.address
            self.display_address = f"{self.wallet_address[:6]}...{self.wallet_address[-4:]}"

    def send_base_tokens(self, to_address, amount_to_send):
        """
        Send native MON tokens to an address.

        Args:
            to_address: Recipient address
            amount: Amount in MON (will be converted to wei)
        """
        if not self.private_key:
            raise ValueError("Private key must be set to execute transactions")

        # amount in wei
        amount = self.w3.to_wei(amount_to_send, 'ether')
        # Prepare transaction data
        logging.info(f"Account {self.wallet_address}: Prepping to send {amount_to_send} MON to {to_address}")

        tx_data = {
            'to': to_address,
            'value': amount,
            'gas': 21000,  # Standard gas limit for simple transfers
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
            'chainId': self.w3.eth.chain_id
        }

        # Sign the transaction
        signed_tx = self.w3.eth.account.sign_transaction(tx_data, self.private_key)

        # Send the transaction
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        gas_used = tx_receipt.gasUsed
        gas_price = self.w3.eth.gas_price
        eth_spent = self.w3.from_wei(gas_used * gas_price, 'ether')

        if tx_receipt.status == 1:
            logging.info(f"Account {self.display_address}: "
                         f"Successfully sent {amount_to_send} MON to {to_address}. Tx fees: {eth_spent:.5f} MON")
        else:
            raise Exception(f"Account {self.display_address}: MON send failed!")

        return tx_hash.hex()

    def get_wallet_balances(self, address: str) -> List[Dict[str, Any]]:
        """
        Get all token balances for a wallet address.

        Args:
            address: The wallet address to check balances for

        Returns:
            List of token balance objects
        """
        url = self.BALANCE_URL.format(address=address)
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")
        return response.json()

    def display_wallet_balances(self, address: Optional[str] = None) -> None:
        """
        Display all token balances for a wallet address in a formatted way.
        MON is always displayed first with max 3 decimal places.

        Args:
            address: The wallet address to check balances for. If None, uses the address from the private key.
        """
        # Use address from private key if not provided
        if address is None:
            if not self.private_key:
                raise ValueError("Either provide an address or set a private key")
            address = self.wallet_address

        balances = self.get_wallet_balances(address)

        # Sort balances so MON is first, then alphabetically by symbol
        balances.sort(key=lambda x: (
            0 if x['symbol'] == 'MON' else 1,  # MON first
            x['symbol']  # Then alphabetically
        ))

        # Build the balance string
        balance_parts = []

        for token in balances:
            if float(token['balance']) > 0:
                symbol = token['symbol']
                if symbol == "MON":
                    formatted_balance = self.get_bal()
                else:
                    formatted_balance = round(float(token['balance']), 3)  # 3 decimal places
                balance_parts.append(f"{formatted_balance} {symbol}")

        # Changed color_print to logging.info since color_print is not defined
        color_print(
            f"Account {self.wallet_address}: Monad Testnet Ecosystem Token Balances: \n{' | '.join(balance_parts)}")

    def get_swap_quote(self, amount: float, from_token: str, to_token: str,
                       sender_address: str, slippage: float = 1,
                       deadline: int = 60, source: str = "fe") -> Dict[str, Any]:
        """
        Get a swap quote from the Monorail pathfinder API.

        Args:
            amount: Amount of tokens to swap (in human-readable form)
            from_token: Token symbol to swap from (MON, WMON, CHOG, etc.)
            to_token: Token symbol to swap to
            sender_address: Address of the transaction sender
            slippage: Maximum acceptable slippage in percentage
            deadline: Transaction deadline in seconds
            source: Source identifier (default 'fe')

        Returns:
            Complete response from the pathfinder API
        """
        # Convert token symbols to addresses
        from_address = self._get_token_address(from_token)
        to_address = self._get_token_address(to_token)

        # Construct API query parameters
        params = {
            "amount": str(amount),
            "from": from_address,
            "to": to_address,
            "slippage": str(slippage),
            "deadline": str(deadline),
            "source": source,
            "sender": sender_address
        }

        # Make the GET request
        headers = get_phantom_headers()
        headers["referer"] = "https://testnet-preview.monorail.xyz/"
        headers['origin'] = "https://testnet-preview.monorail.xyz/"

        response = requests.get(self.BASE_URL, params=params, headers=headers)
        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")

        return response.json()

    def build_swap_transaction(self, amount: float, from_token: str, to_token: str,
                               sender_address: str) -> Dict[str, Any]:
        """
        Build a swap transaction for the given token pair.

        Args:
            amount: Amount of tokens to swap (in human-readable form)
            from_token: Token symbol to swap from
            to_token: Token symbol to swap to
            sender_address: Address of the transaction sender

        Returns:
            Transaction object ready to be signed and sent
        """
        quote = self.get_swap_quote(amount, from_token, to_token, sender_address)

        # Extract transaction details from the quote - updated for new response format
        tx_data = quote['transaction']

        # Prepare the transaction
        transaction = {
            'from': sender_address,
            'to': tx_data['to'],
            'data': tx_data['data'],
            'value': int(tx_data['value'], 16) if isinstance(tx_data['value'], str) and tx_data['value'].startswith(
                '0x') else int(tx_data['value']),
            'nonce': self.w3.eth.get_transaction_count(sender_address),
            'chainId': 10143  # Monad testnet chain ID
        }

        # Use the gas estimated from quote if available, otherwise use a reasonable estimate
        # Let the node estimate the gas to avoid hardcoding
        try:
            transaction['gas'] = self.w3.eth.estimate_gas(transaction)
        except Exception:
            # Fallback to a conservative estimate if estimation fails
            transaction['gas'] = 300000

        # Add appropriate gas price parameters
        block = self.w3.eth.get_block('latest')
        if hasattr(block, 'baseFeePerGas') and block.baseFeePerGas is not None:
            # Use EIP-1559 style gas parameters
            transaction['maxFeePerGas'] = int(block.baseFeePerGas * 1.5)
            transaction['maxPriorityFeePerGas'] = int(self.w3.eth.gas_price * 0.1)
        else:
            # Use legacy gas price
            transaction['gasPrice'] = self.w3.eth.gas_price

        return transaction

    def execute_swap(self, amount: float, from_token: str, to_token: str) -> str:
        """
        Execute a token swap with the given parameters. If transaction fails,
        retry up to 3 times with increased gas.

        Args:
            amount: Amount of tokens to swap (in human-readable form)
            from_token: Token symbol to swap from
            to_token: Token symbol to swap to

        Returns:
            Transaction hash of the executed swap

        Raises:
            ValueError: If private key is not set
            Exception: If all retry attempts fail
        """
        if not self.private_key:
            raise ValueError("Private key must be set to execute transactions")

        # Use the class attributes instead of recreating them
        sender_address = self.wallet_address

        # Updated to use the new estimate_max_output function
        estimate = self.estimate_max_output(from_token, to_token, amount)
        expected_output = estimate['output_amount']

        # Build the transaction
        transaction = self.build_swap_transaction(amount, from_token, to_token, sender_address)

        # Set up retry logic
        max_retries = 1
        gas_multiplier_increment = 0.2  # Increase gas by 20% each retry
        gas_multiplier = 1.0

        for attempt in range(1, max_retries + 1):
            try:
                # On retries, adjust the gas parameters
                if attempt > 1:
                    gas_multiplier += gas_multiplier_increment
                    logging.info(
                        f"Account {self.display_address}: Retry #{attempt - 1} with {int(gas_multiplier * 100)}% gas")

                    # Increase gas limit
                    if 'gas' in transaction:
                        transaction['gas'] = int(transaction['gas'] * gas_multiplier)

                    # Increase gas price or priority fee depending on type
                    if 'maxFeePerGas' in transaction and 'maxPriorityFeePerGas' in transaction:
                        transaction['maxFeePerGas'] = int(transaction['maxFeePerGas'] * gas_multiplier)
                        transaction['maxPriorityFeePerGas'] = int(transaction['maxPriorityFeePerGas'] * gas_multiplier)
                    elif 'gasPrice' in transaction:
                        transaction['gasPrice'] = int(transaction['gasPrice'] * gas_multiplier)

                    # Update nonce in case previous transaction was mined
                    transaction['nonce'] = self.w3.eth.get_transaction_count(sender_address)

                # Sign the transaction
                signed_tx = self.w3.eth.account.sign_transaction(transaction, self.private_key)

                # Send the transaction
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                nonce = transaction['nonce']
                mon_bal = self.get_bal()

                logging.info(
                    f"Account {self.display_address}: Bal {mon_bal} MON. Transaction #{nonce} sent! Hash: 0x{tx_hash.hex()}")

                # Wait for transaction to be mined
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                gas_used = tx_receipt.gasUsed
                eth_spent = self.w3.from_wei(gas_used * self.w3.eth.gas_price, 'ether')

                # Check if transaction succeeded
                if tx_receipt.status == 1:
                    logging.info(
                        f"Account {self.display_address}: Successfully swapped {amount} {from_token} -> {expected_output} {to_token}. Tx fees: {eth_spent:.5f} MON")
                    return tx_hash.hex()
                else:
                    logging.warning(
                        f"Account {self.display_address}: Transaction mined but failed with status 0. Attempt {attempt}/{max_retries}. Hash: 0x{tx_hash.hex()}. Tx fees: {eth_spent:.5f} MON")

                    # On last retry, raise exception
                    if attempt == max_retries:
                        raise Exception(
                            f"Account {self.display_address}: Failed to swap {amount} {from_token} -> {expected_output} {to_token} after {max_retries} attempts. Hash: 0x{tx_hash.hex()}")

                    # Continue to next retry
                    continue

            except Exception as e:
                if attempt == max_retries:
                    logging.error(f"Account {self.display_address}: All {max_retries} swap attempts failed: {str(e)}")
                    raise Exception(
                        f"Account {self.display_address}: Failed to swap {amount} {from_token} -> {expected_output} {to_token} after {max_retries} attempts: {str(e)}")
                elif "Signer had insufficient balance" in str(e):
                    raise e
                else:
                    logging.warning(
                        f"Account {self.display_address}: Swap attempt {attempt} failed: {str(e)}. Retrying...")
                    # Sleep briefly before retrying
                    time.sleep(2)

        # This should never be reached due to exceptions in the loop
        raise Exception("Unexpected error: reached end of execute_swap without success or exception")

    def calculate_token_price(self, base_token: str, quote_token: str, amount: float = 1.0) -> float:
        """
        Calculate the price of one token in terms of another.

        Args:
            base_token: The token to get the price for (e.g., 'CHOG')
            quote_token: The token to express the price in (e.g., 'USDC')
            amount: The amount of base tokens to get quote for

        Returns:
            The price of base_token in terms of quote_token
        """
        # Use a dummy address for the sender
        dummy_address = "0x0000000000000000000000000000000000000000"

        # Get the quote
        quote = self.get_swap_quote(amount, base_token, quote_token, dummy_address)

        # Extract the output amount - updated for new response format
        output_amount = float(quote['output']) / 10 ** 18  # Assuming the value is in wei format

        # Calculate and return the price
        return output_amount / amount

    def estimate_max_output(self, from_token: str, to_token: str, input_amount: float) -> Dict[str, Any]:
        """
        Estimate the maximum output amount and route details for a swap.

        Args:
            from_token: Token to swap from
            to_token: Token to swap to
            input_amount: Amount of from_token to swap

        Returns:
            Dictionary with output amount, route details, and more
        """
        # Use a dummy address for the sender
        dummy_address = "0x0000000000000000000000000000000000000000"

        # Get the quote
        quote = self.get_swap_quote(input_amount, from_token, to_token, dummy_address)

        # Extract relevant information - updated for new response format
        result = {
            'input_amount': input_amount,
            'output_amount': float(quote['output']) / 10 ** 18,  # Convert from wei
            'min_output_amount': float(quote['min_output']) / 10 ** 18,  # Convert from wei
            'hops': quote['hops'],
            'effective_price': float(quote['output']) / (float(quote['input']) or 1)  # Calculate price ratio
        }

        return result

    def _get_token_address(self, token: str) -> str:
        """
        Get the address for a token symbol.

        Args:
            token: Token symbol (case-insensitive)

        Returns:
            Token address

        Raises:
            ValueError: If token is not recognized
        """
        token_upper = token
        if token_upper in self.TOKENS:
            return self.TOKENS[token_upper]

        # If it already looks like an address, return it
        if token.startswith('0x') and len(token) == 42:
            return token.lower()

        raise ValueError(f"Unknown token: {token}. Available tokens: {', '.join(self.TOKENS.keys())}")

    def get_bal(self):
        # get MON bal
        balance = self.w3.eth.get_balance(self.wallet_address)
        balance_eth = round(self.w3.from_wei(balance, 'ether'), 3)
        return balance_eth
