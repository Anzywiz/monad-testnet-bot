from src.logger import logging
from src.swapper import MonadSwapper


class MonadStaker(MonadSwapper):  # Inheriting from MonadSwapper
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

        logging.info(f"Account {self.display_address}: Bal {mon_bal} MON. Transaction #{nonce} sent! Hash: 0x{tx_hash_hex}")

        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        gas_used = tx_receipt.gasUsed
        gas_price = self.w3.eth.gas_price
        eth_spent = self.w3.from_wei(gas_used * gas_price, 'ether')

        if tx_receipt["status"] == 1:
            logging.info(f"Account {self.display_address}: Success! {success_message}. Tx fees: {eth_spent:.5f} MON")
            return '0x' + tx_hash_hex
        else:
            logging.error(f"Account {self.display_address}: Transaction failed. Tx fees: {eth_spent:.5f} MON")
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
            'type': 2,  # EIP-1559 transaction
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
