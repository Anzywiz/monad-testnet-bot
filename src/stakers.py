"""Programmatically stake on several some dApps (Kinstu, apriori, magma)"""

from src.monorail import MonorailSwapper
import asyncio
import random
import logging
from web3.exceptions import Web3RPCError

from utils import timeout, get_web3_connection, private_keys, data
from logger import color_print

# Constants
DAILY_STAKES = data["DAILY_INTERACTION"]["STAKERS"]
FUND_AMT = data["FUND_AMOUNT"]
FUNDER_PRIVATE_KEY = data["FUNDER_PRIVATE_KEY"]
STAKERS = data["STAKERS"]
STAKING_METHODS = [f"{i}_stake" for i in STAKERS]


def get_random_stake_amount():
    # Generate a random value between 0.0001 and 0.001
    rand_int = random.randint(1, 100)
    random_swap_amt = float(f"0.000{rand_int}")
    return random_swap_amt


class MonadStaker(MonorailSwapper):  # Inheriting attributes and method from MonadSwapper
    def __init__(self, w3, private_key):
        """
        Initialize a MonadStaker with your private key

        Args:
            private_key (str): Private key of the wallet to stake from
        """
        super().__init__(w3, private_key)  # Call parent constructor

        # Contract addresses
        self.kintsu_contract = "0x07AabD925866E8353407E67C1D157836f7Ad923e"
        self.apriori_contract = "0xb2f82D0f38dc453D596Ad40A37799446Cc89274A"
        self.magma_contract = "0x2c9C959516e9AAEdB2C748224a41249202ca8BE7"

        # ABIs for the staking functions
        self.kintsu_abi = [
            {
                "inputs": [],
                "name": "stake",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            }
        ]

        self.apriori_abi = [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "address", "name": "receiver", "type": "address"}
                ],
                "name": "deposit",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            }
        ]

        # For debugging
        self.debug_mode = False

    def kintsu_stake(self, amount_to_stake):
        """
        Stake MON tokens to receive sMON tokens through Kintsu

        Args:
            amount_to_stake (float): Amount of MON to stake in ether units

        Returns:
            str: Transaction hash if successful, None otherwise
        """
        contract = self.w3.eth.contract(address=self.kintsu_contract, abi=self.kintsu_abi)

        # Convert amount to wei
        stake_amount_wei = self.w3.to_wei(amount_to_stake, 'ether')

        # Get current nonce
        nonce = self.w3.eth.get_transaction_count(self.wallet_address)

        # Build transaction
        txn = contract.functions.stake().build_transaction({
            'from': self.wallet_address,
            'value': stake_amount_wei,
            'gas': 100000,
            'maxFeePerGas': self.w3.to_wei(50, 'gwei'),
            'maxPriorityFeePerGas': self.w3.to_wei(2, 'gwei'),
            'nonce': nonce,
            'chainId': self.w3.eth.chain_id,
            'type': 2  # EIP-1559 transaction
        })

        # Sign and send transaction
        return self._sign_and_send_transaction(txn, f"Staked {amount_to_stake} MON for sMON via Kintsu")

    def apriori_stake(self, amount_to_stake):
        """
        Stake MON tokens to receive aprMON tokens through Apriori

        Args:
            amount_to_stake (float): Amount of MON to stake in ether units

        Returns:
            str: Transaction hash if successful, None otherwise
        """
        # Create contract instance
        contract = self.w3.eth.contract(address=self.apriori_contract, abi=self.apriori_abi)

        # Convert amount to wei - ensure it's exactly the same amount as in the transaction
        stake_amount_wei = self.w3.to_wei(amount_to_stake, 'ether')

        # Get current nonce
        nonce = self.w3.eth.get_transaction_count(self.wallet_address)

        # Build transaction
        txn = contract.functions.deposit(
            stake_amount_wei,
            self.wallet_address  # receiver is the same as sender
        ).build_transaction({
            'from': self.wallet_address,
            'value': stake_amount_wei,
            'gas': 100000,
            'maxFeePerGas': self.w3.to_wei(50, 'gwei'),
            'maxPriorityFeePerGas': self.w3.to_wei(2, 'gwei'),
            'nonce': nonce,
            'chainId': self.w3.eth.chain_id,
            'type': 2  # EIP-1559 transaction
        })

        # Sign and send transaction
        return self._sign_and_send_transaction(txn, f"Staked {amount_to_stake} MON for aprMON via Apriori")

    def _sign_and_send_transaction(self, transaction, success_message):
        """Helper method to sign and send a transaction"""
        # Sign transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)

        # Send transaction
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_hash_hex = tx_hash.hex()

        nonce = transaction["nonce"]
        mon_bal = self.get_bal()

        logging.info(f"👤 {self.display_address}: Bal {mon_bal} MON. Transaction #{nonce} sent! Hash: 0x{tx_hash_hex}")

        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        gas_used = tx_receipt.gasUsed
        gas_price = self.w3.eth.gas_price
        eth_spent = self.w3.from_wei(gas_used * gas_price, 'ether')

        if tx_receipt["status"] == 1:
            logging.info(f"👤 {self.display_address}: Success! {success_message}. Tx fees: {eth_spent:.5f} MON")
            return '0x' + tx_hash_hex
        else:
            logging.error(f"👤 {self.display_address}: Transaction failed. Tx fees: {eth_spent:.5f} MON")
            return None

    def build_base_transaction(self):
        # Get current nonce
        nonce = self.w3.eth.get_transaction_count(self.wallet_address)

        # Build raw transaction with the provided function selector
        txn = {
            'from': self.wallet_address,
            'gas': 100000,
            'maxFeePerGas': self.w3.to_wei(50, 'gwei'),
            'maxPriorityFeePerGas': self.w3.to_wei(2, 'gwei'),
            'nonce': nonce,
            'chainId': self.w3.eth.chain_id,
            'type': 2
        }
        return txn

    def magma_stake(self, amount_to_stake):
        function_selector = '0xd5575982'
        # Convert amount to wei
        stake_amount_wei = self.w3.to_wei(amount_to_stake, 'ether')

        # Build raw transaction with the provided function selector
        base_txn = self.build_base_transaction()
        remaining_txn = {
            'to': self.magma_contract,
            'value': stake_amount_wei,
            'data': function_selector,  # Direct function selector without ABI
        }
        txn = {**base_txn, **remaining_txn}

        # Sign and send transaction
        return self._sign_and_send_transaction(txn, f"Staked {amount_to_stake} MON for gMON via Magma")

    def magma_unstake(self, amount_to_unstake):
        unstake_amount_wei = self.w3.to_wei(amount_to_unstake, 'ether')

        # Get current nonce
        nonce = self.w3.eth.get_transaction_count(self.wallet_address)

        # Create function selector and parameter
        function_selector = "0x6fed1ea7"

        # Encode the parameter (amount in wei) as a 32-byte hex string
        # First convert to hex, remove '0x', and pad to 64 characters (32 bytes)
        hex_amount = hex(unstake_amount_wei)[2:].zfill(64)

        # Combine function selector and parameter
        data = function_selector + hex_amount

        base_txn = self.build_base_transaction()
        remaining_txn = {
            'to': self.magma_contract,
            'value': 0,
            'data': data,
            'nonce': nonce
        }
        txn = {**base_txn, **remaining_txn}

        # Sign and send transaction
        return self._sign_and_send_transaction(txn, f"Un-staked {amount_to_unstake} gMON for MON via Magma")


async def stake_token(private_key, cycles=DAILY_STAKES):
    count = 0
    while True:  # Infinite loop, till you interrupt
        try:
            # Initialize the swapper
            staker = MonadStaker(get_web3_connection(), private_key)

            try:
                # Define possible staking methods
                staking_methods = STAKING_METHODS
                if not staking_methods:
                    return
                random.shuffle(staking_methods)
                for method_name in staking_methods:
                    if method_name == "kintsu_stake":
                        # Get a random amount greater than 0.01
                        rand_int = random.randint(1, 2)
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

                # after all thestaking for loop has been completed
                count += 1
                logging.info(f"👤 {staker.display_address}: Stake count: {count}/{cycles}..")

                if count >= cycles:
                    logging.info(f"👤 {staker.display_address}: Full Stake cycle complete.")
                    return
                else:
                    await timeout(60, 200)

            except Web3RPCError as e:
                # Error handling as before
                if 'Signer had insufficient balance' in str(e):
                    logging.warning(
                        f"👤 {staker.display_address}: Signer had insufficient balance. Funding from Fund wallet..")
                    # initialise funder
                    funder = MonadStaker(get_web3_connection(), FUNDER_PRIVATE_KEY)
                    funder.send_base_tokens(staker.wallet_address, FUND_AMT)
                else:
                    logging.error(f"Error {e}. Trying again..")
                    await asyncio.sleep(5)

        except Exception as e:
            color_print(f"An error occurred within the infinite loop\n{e}", "RED")
            color_print(f"Restarting Monad staker...", "MAGENTA")
            await asyncio.sleep(1 * 60 * 60)


async def run():
    """Run staker with multiple private keys from private_keys.txt."""

    if not private_keys:
        logging.error("No private keys found in private_keys.txt!")
        color_print("ERROR: No private keys found in private_keys.txt!", "RED")
        return

    color_print(f"Starting Monad Staker with {len(private_keys)} accounts...", "GREEN")

    # Create tasks for each private key
    tasks = []
    for private_key in private_keys:
        tasks.append(stake_token(private_key))

    # Run all tasks concurrently
    await asyncio.gather(*tasks)


if __name__ == "__main__":

    print("Starting Monad staker script...")
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nScript stopped by user")
    except Exception as e:
        logging.critical(f"Fatal error: {str(e)}")
        print(f"\nFatal error: {str(e)}")