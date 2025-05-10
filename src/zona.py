from src.stakers import MonadStaker
import logging
from utils import get_web3_connection, private_keys, data
from logger import color_print
import random
import asyncio
from web3.exceptions import Web3RPCError

# Constants
FUND_AMT = data["FUND_AMOUNT"]
FUNDER_PRIVATE_KEY = data["FUNDER_PRIVATE_KEY"]


class ZonaBet(MonadStaker):  # Inheriting attributes and method from MonadStaker
    def __init__(self, w3, private_key):
        """
        Initialize a MonadStaker with your private key

        Args:
            private_key (str): Private key of the wallet to stake from
        """
        super().__init__(w3, private_key)  # Call parent constructor

    def zona_bet(self, amount_to_bet):
        """Place a bet on Zona Finance with the specified amount."""
        # Convert amount to wei
        bet_amount_wei = self.w3.to_wei(amount_to_bet, 'ether')

        # Convert bet amount to hex format with padding to 32 bytes
        bet_amount_hex = hex(bet_amount_wei)[2:].zfill(64)

        # Construct the transaction data with the correct bet amount
        # Function selector (0x2c68cda2) + parameters
        # Replacing only the bet amount parameter while keeping other parameters intact
        tx_data = (
                "0x2c68cda2"  # Function selector
                + "0000000000000000000000000000000000000000000000000000000000000000"  # First parameter (uint8)
                + "00000000000000000000000000000000000000000000000000000000000000a0"  # Second parameter (bytes offset)
                + "0000000000000000000000000000000000000000000000000000000000000000"  # Third parameter
                + "0000000000000000000000000000000000000000000000000000000000000000"  # Fourth parameter
                + bet_amount_hex  # Fifth parameter (bet amount in wei)
                + "0000000000000000000000000000000000000000000000000000000000000008"  # String length
                + "686f6e676b6f6e67000000000000000000000000000000000000000000000000"  # "hongkong" padded
        )

        ZONA_CONTRACT_ADDRESS = "0xf7efcB69E4D2E3f254ac57DF2C64c12CE381aeda"

        # Build base transaction
        base_txn = self.build_base_transaction()

        # Estimate gas
        try:
            gas_estimate = self.w3.eth.estimate_gas({
                'to': ZONA_CONTRACT_ADDRESS,
                'from': self.wallet_address,
                'data': tx_data,
                'value': bet_amount_wei
            })

            # Add some buffer to the gas estimate
            gas_with_buffer = int(gas_estimate * 1.1)

            # Construct the full transaction
            txn = {
                **base_txn,
                'to': ZONA_CONTRACT_ADDRESS,
                'value': bet_amount_wei,
                'data': tx_data,
                'gas': gas_with_buffer
            }

            # Sign and send transaction
            return self._sign_and_send_transaction(txn, f"Bet {amount_to_bet} MON on zona finance success!")

        except Exception as e:
            logging.error(f"Gas estimation failed: {e}")
            # You could implement fallback logic here if needed
            raise

    def zona_resolve_bet(self):

        # Build raw transaction with the provided function selector
        base_txn = self.build_base_transaction()

        # Override the gas value from base_txn
        # base_txn['gas'] = 150000

        remaining_txn = {
            'to': '0xf7efcB69E4D2E3f254ac57DF2C64c12CE381aeda',
            'value': 0,
            'data': '0x0d19e9a10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008686f6e676b6f6e67000000000000000000000000000000000000000000000000'
            # 1 hr false: is 8min wait
        }
        txn = {**base_txn, **remaining_txn}

        gas_estimate = self.w3.eth.estimate_gas(txn)
        txn['gas'] = gas_estimate

        # Sign and send transaction
        return self._sign_and_send_transaction(txn, f"Bet resolved on zona finance successfully")


async def place_bet(private_key):
    """Place a single bet using the provided private key."""
    try:
        # Initialize the betting class
        bet = ZonaBet(get_web3_connection(), private_key)

        try:
            # Get a random bet amount between 0.001 and 0.005
            bet_amount = float(f"0.00{random.randint(1, 5)}")

            # Place the bet
            color_print(f"Account {bet.display_address}: Preparing to bet {bet_amount} tokens")
            bet.zona_bet(bet_amount)
            logging.info(f"Account {bet.display_address}: Placed bet successfully.")

        except Web3RPCError as e:
            if 'Signer had insufficient balance' in str(e):
                logging.warning(
                    f"Account {bet.display_address}: Signer had insufficient balance. Funding from Fund wallet.."
                )
                # Initialize funder
                funder = ZonaBet(get_web3_connection(), FUNDER_PRIVATE_KEY)
                funder.send_base_tokens(bet.wallet_address, FUND_AMT)
                # Try again after funding
                await asyncio.sleep(30)
                bet.zona_bet(bet_amount)
            elif '0x08c379a000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000039506f736974696f6e206973206e6f74207265736f6c7661626c65202861637475616c2076616c7565206e6f742079657420757064617465642900000000000000' in str(
                    e):
                # Handle the specific error mentioned in your example
                logging.warning(
                    f"Account {bet.display_address}: Position is not resolvable (actual value not yet updated)")
            else:
                logging.error(f"Account {bet.display_address}: Error {e}")

    except Exception as e:
        color_print(f"Account {bet.display_address}: An error occurred: {e}", "RED")


async def run():
    """Run bets with multiple private keys from private_key.txt."""

    if not private_keys:
        logging.error("No private keys found in private_key.txt!")
        color_print("ERROR: No private keys found in private_key.txt!", "RED")
        return

    color_print(f"Starting Zona Bet with {len(private_keys)} accounts...", "GREEN")

    # Create tasks for each private key
    tasks = []
    for private_key in private_keys:
        tasks.append(place_bet(private_key))

    # Run all tasks concurrently
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    print("Starting Zona betting script...")
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nScript stopped by user")
    except Exception as e:
        logging.critical(f"Fatal error: {str(e)}")
        print(f"\nFatal error: {str(e)}")
