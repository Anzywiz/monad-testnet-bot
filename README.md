# Monad Interaction Bot

If you're farming the Monad testnet and want to automate interactions across multiple accounts, this bot is for you. It supports interacting with contracts from several ecosystems, including Apriori, Magma, and Kinstu staking. The swap functionality is based on Monorail's API. If there are any bugs, they originate from Monorail and will be resolved in due time.

## 🚀 Features

- Auto interaction across several Monad ecosystems.

* Displays verified tokens held across all ecosystems on Monad.
* Auto swapping and staking with random amounts and wait times to mimic human interaction.
* Supports multiple accounts and proxy integration.
* Auto-funding from a primary account with sufficient MON balance.
* Configurable daily swap and staking cycles.
* Colored display for improved readability.

## 📌 Setup

Follow these steps to set up and run the bot.

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Anzywiz/monad-testnet-bot.git
cd monad-testnet-bot
```

### 2️⃣ Create and Activate a Virtual Environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure the Bot

Create a `config.json` file in the project directory with the following structure:

```json
{
  "PRIVATE_KEYS": [
      "0x123..."
  ],
  "FUNDER_PRIVATE_KEY": "",
  "PROXIES": "",
  "GITHUB_USERNAME": "",
  "FUND_AMOUNT": 0.5,
  "DAILY_SWAP_CYCLES": 5,
  "STAKE_CYCLES": 5
}
```

- **PRIVATE\_KEYS**: List of private keys for the accounts you want to use.
- **FUNDER\_PRIVATE\_KEY**: The private key of the account that will fund your other accounts with MON.
- **PROXIES**: Proxy URL (if applicable) for enhanced anonymity. The format for proxies should be:
  - Without authentication: `"proxies": "http://123.456.78.90:8080"`
  - With authentication: `"proxies": "http://user:pass@123.456.78.90:8080"`
- **GITHUB\_USERNAME**: Your GitHub username (starring the repo is required).
- **FUND\_AMOUNT**: The amount of MON to send per funding cycle.
- **DAILY\_SWAP\_CYCLES**: Number of swap transactions executed daily.
- **STAKE\_CYCLES**: Number of staking transactions executed daily.

### 5️⃣ Run the Bot

```bash
python main.py
```

## 🔄 Updates

Stay tuned for updates and new features!

## 🛠 Issues & Contributions

- If you encounter any issues, report them in the Issues section.
- Want to improve the bot? Fork the repository, make your changes, and submit a pull request!

## 📜 License

This project is licensed under the MIT License.

## 🤔 Why This Bot?

I noticed that most Monad scripts create false interactions when I checked and verified the hash. This bot ensures genuine and verifiable interactions across multiple ecosystems.

⭐ Don't forget to star the repo if you find it useful! Your support helps keep the project growing! 😊

