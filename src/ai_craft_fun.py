import requests
import json
import time
from eth_account.messages import encode_defunct
from web3 import Web3
from src.proxies import get_phantom_headers
from src.staker import MonadStaker, logging


class AiCraftFun(MonadStaker):
    def __init__(self, w3, private_key):
        """
        Initialize aicraft.fun with your private key

        Args:
            w3: Web3 instance connected to Monad testnet
            private_key (str): Private key of wallet you want to automate

        """
        super().__init__(w3, private_key)  # Call parent constructor

        self.w3 = w3
        self.private_key = private_key
        self.wallet_address = self.w3.eth.account.from_key(private_key).address
        self.display_address = f"{self.wallet_address[:4]}...{self.wallet_address[-4:]}"
        self.base_url = "https://api.aicraft.fun"
        self.token = None
        self.headers = get_phantom_headers()

    def sign_message(self, message):
        """Sign a message with the private key"""
        message_hash = encode_defunct(text=message)
        signed_message = self.w3.eth.account.sign_message(message_hash, private_key=self.private_key)
        return '0x' + signed_message.signature.hex()

    def send_transaction(self, contract_address, abi, function_name, params):
        """Build and send a transaction to the blockchain"""
        try:
            # Convert contract address to checksum format
            checksum_address = self.w3.to_checksum_address(contract_address)
            contract = self.w3.eth.contract(address=checksum_address, abi=abi)

            # Get function from contract
            contract_function = getattr(contract.functions, function_name)

            # Build function call with parameters
            function_call = contract_function(*params)

            # Get current gas price with a slight increase
            gas_price = self.w3.eth.gas_price

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.wallet_address)
            tx = function_call.build_transaction({
                'from': self.wallet_address,
                'nonce': nonce,
                'gas': 120000,
                'gasPrice': gas_price
            })

            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)

            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = '0x' + tx_hash.hex()

            # Wait for transaction to be mined
            logging.info(f"Account {self.display_address}: Bal. {self.get_bal()} MON.  #{nonce} sent!: {tx_hash_hex}")
            logging.info(f"Account {self.display_address}: Waiting for transaction to be mined...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            logging.info(f"Account {self.display_address}: Transaction mined! Status: {'Success' if receipt.status == 1 else 'Failed'}")

            # Return transaction hash
            return tx_hash_hex

        except Exception as e:
            logging.error(f"Error in transaction: {str(e)}")
            raise

    def get_sign_in_msg(self):
        """Get the sign-in message to be signed"""
        url = f"{self.base_url}/auths/wallets/sign-in/message?address={self.wallet_address}&type=ETHEREUM_BASED"
        response = requests.get(url)
        data = response.json()
        return data['data']['message']

    def sign_in(self, ref_code=None):
        """Sign in to get auth token using wallet signature"""
        # Get message to sign
        message = self.get_sign_in_msg()

        # Sign the message with private key
        signature = self.sign_message(message)

        # Prepare payload
        payload = {
            "address": self.wallet_address,
            "signature": signature,
            "message": message,
            "type": "ETHEREUM_BASED"
        }

        # Add referral code if provided
        if ref_code:
            payload["refCode"] = ref_code

        # Send sign-in request
        url = f"{self.base_url}/auths/wallets/sign-in"
        response = requests.post(url, json=payload)

        if response.status_code == 200 or response.status_code == 201:
            logging.info(f"Account {self.display_address}: User sign in success!")
            data = response.json()
        else:
            raise Exception(f"Error during sign in {response.status_code} {response.text}")

        # Store token for future requests
        self.token = data['data']['token']
        self.headers["Authorization"] = f"Bearer {self.token}"

        return data

    def get_candidates(self, project_id):
        """Get list of candidates for a specific project"""
        url = f"{self.base_url}/candidates?projectID={project_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def set_referral_code(self, ref_code):
        """Set referral code for user"""
        url = f"{self.base_url}/users/referral"
        payload = {"refCode": ref_code}
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()

    def get_user_info(self):
        """Get user information including wallet ID needed for voting"""
        url = f"{self.base_url}/users/me?includePresalePurchasedAmount=true"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def create_feed_order(self, candidate_id, wallet_id, feed_amount=1, chain_id="10143", ref_code=None):
        """Create a feed order to get transaction data for voting"""
        url = f"{self.base_url}/feeds/orders"
        payload = {
            "candidateID": candidate_id,
            "walletID": wallet_id,
            "feedAmount": feed_amount,
            "chainID": chain_id
        }

        if ref_code:
            payload["refCode"] = ref_code

        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()

    def confirm_transaction(self, order_id, tx_hash, ref_code=None):
        """Confirm transaction after sending to blockchain"""
        url = f"{self.base_url}/feeds/orders/{order_id}/confirm"
        payload = {
            "transactionHash": tx_hash
        }

        if ref_code:
            payload["refCode"] = ref_code

        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()

    def vote_for_candidate(self, candidate_id, ref_code=None, feed_amount=1):
        """Complete full voting process for a candidate with proper message signing"""
        # 1. Ensure we're signed in
        if not self.token:
            self.sign_in(ref_code)

        # 2. Get user info to find wallet ID
        user_info = self.get_user_info()
        wallet_id = user_info['data']['wallets'][0]['_id']

        # 3. Set referral code if provided
        if ref_code:
            self.set_referral_code(ref_code)

        # 4. Check if your daily votes have been exceeded
        daily_feed_count = user_info['data'].get('todayFeedCount', 0)
        if daily_feed_count <= 0:
            raise Exception(f"Cannot create order! You've exceeded your remaining vote count")

        # 5. Create feed/vote order to get transaction data
        order_response = self.create_feed_order(
            candidate_id=candidate_id,
            wallet_id=wallet_id,
            feed_amount=feed_amount,
            ref_code=ref_code
        )

        try:
            # Extract necessary transaction data
            payment_data = order_response['data']['payment']
            contract_address = payment_data['contractAddress']
            abi = payment_data['abi']
            function_name = payment_data['functionName']

            # Extract the userHashedMessage and sign it
            user_hashed_message = payment_data['params']['userHashedMessage']

            # Sign the message using web3
            signature = self.w3.eth.account.sign_message(
                encode_defunct(hexstr=user_hashed_message),
                private_key=self.private_key
            ).signature

            # Prepare parameters for transaction with our signature
            params = [
                payment_data['params']['candidateID'],
                payment_data['params']['feedAmount'],
                payment_data['params']['requestID'],
                payment_data['params']['requestData'],
                signature,  # Use our own signature of the userHashedMessage
                bytes.fromhex(payment_data['params']['integritySignature'][2:])
            ]

            contract_address = self.w3.to_checksum_address(contract_address)

            # Send transaction to blockchain
            tx_hash = self.send_transaction(
                contract_address=contract_address,
                abi=abi,
                function_name=function_name,
                params=params
            )

            # Confirm transaction in API
            order_id = payment_data['params']['requestID']
            confirmation = self.confirm_transaction(
                order_id=order_id,
                tx_hash=tx_hash,
                ref_code=ref_code
            )

            if confirmation["statusCode"] == 201:
                user_info = self.get_user_info()  # get updated points

            points = user_info['data']["point"]
            today_feed_count = user_info['data']["todayFeedCount"]
            logging.info(f"Account {self.display_address}: Point {points} | Votes left {today_feed_count}")
            return confirmation
        except KeyError:
            if order_response["description"] == "Exceed remaining feed count":
                raise Exception(f"Cannot create order! You've exceeded your remaining vote count")

    def get_top_candidates(self, project_id, category=None, limit=10):
        """Get top candidates by feed count, optionally filtered by category"""
        candidates = self.get_candidates(project_id)
        candidate_list = candidates['data']

        # Filter by category if specified
        if category:
            candidate_list = [c for c in candidate_list if c['category']['name'] == category]

        # Sort by feed count (votes)
        sorted_candidates = sorted(candidate_list, key=lambda x: x['feedCount'], reverse=True)

        # Return top candidates
        return sorted_candidates[:limit]

    def auto_vote(self, project_id, ref_code, top_n=5):
        """Automatically vote for top N candidates in a project"""
        # Sign in with referral code
        if not self.token:
            self.sign_in(ref_code)

        # Get top candidates
        top_candidates = self.get_top_candidates(project_id, limit=top_n)

        results = []
        for candidate in top_candidates:
            try:
                result = self.vote_for_candidate(
                    candidate_id=candidate['_id'],
                    ref_code=ref_code
                )
                results.append({
                    'candidate': candidate['name'],
                    'success': True,
                    'result': result
                })
                # Sleep to avoid rate limiting
                time.sleep(2)
            except Exception as e:
                results.append({
                    'candidate': candidate['name'],
                    'success': False,
                    'error': str(e)
                })

        return results

    def vote_by_country(self, project_id, ref_code, country_code, feed_amount=1):
        """Vote for a candidate from a specific country"""
        # Sign in
        if not self.token:
            self.sign_in(ref_code)

        # Get all candidates
        candidates = self.get_candidates(project_id)
        candidate_list = candidates['data']

        # Find candidate from specified country
        country_candidates = [c for c in candidate_list if 'metadata' in c and
                              'countryCode' in c['metadata'] and
                              c['metadata']['countryCode'] == country_code]

        if not country_candidates:
            return {"success": False, "error": f"No candidate found for country code {country_code}"}

        # Sort by feed count and pick the top one
        top_candidate = sorted(country_candidates, key=lambda x: x['feedCount'], reverse=True)[0]

        # Vote for the candidate
        try:
            result = self.vote_for_candidate(
                candidate_id=top_candidate['_id'],
                ref_code=ref_code,
                feed_amount=feed_amount
            )
            return {
                "success": True,
                "country": country_code,
                "candidate": top_candidate['name'],
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "country": country_code,
                "candidate": top_candidate['name'],
                "error": str(e)
            }

    def daily_votes(self, project_id, ref_code, countries=None):
        """Use daily voting limit on specified countries or top candidates"""
        # Sign in
        if not self.token:
            self.sign_in(ref_code)

        # Get user info to check daily vote limit
        user_info = self.get_user_info()
        daily_feed_count = user_info['data'].get('todayFeedCount', 0)
        # remaining_votes = 20 - daily_feed_count  # Assuming 20 is the daily limit
        remaining_votes = daily_feed_count

        if remaining_votes <= 0:
            return {"success": False, "error": "Daily voting limit reached"}

        results = []
        import random

        if countries:
            # Vote for specific countries
            for vote in range(remaining_votes):
                country = random.choice(countries)
                result = self.vote_by_country(project_id, ref_code, country)
                results.append(result)
                time.sleep(2)  # Avoid rate limiting
        else:
            # Vote for top candidates
            top_candidates = self.get_top_candidates(project_id, limit=remaining_votes)
            for candidate in top_candidates:
                try:
                    result = self.vote_for_candidate(
                        candidate_id=candidate['_id'],
                        ref_code=ref_code
                    )
                    results.append({
                        "success": True,
                        "candidate": candidate['name'],
                        "result": result
                    })
                    time.sleep(2)  # Avoid rate limiting
                except Exception as e:
                    results.append({
                        "success": False,
                        "candidate": candidate['name'],
                        "error": str(e)
                    })

        return {
            "votes_used": len(results),
            "remaining_votes": max(0, remaining_votes - len(results)),
            "results": results
        }
