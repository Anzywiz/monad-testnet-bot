# Monad Interaction Bot

If you're farming the Monad testnet and want to automate interactions, this bot is for you. It supports interacting with contracts from several ecosystems, including Apriori, Magma, and Kinstu staking. The swap functionality is based on Monorail's API. If there are any bugs, they originate from Monorail and will be resolved in due time.

![bot dashboard](https://github.com/Anzywiz/monad-testnet-bot/blob/main/img/bot%20dashbord.png)

## 🚀 Features

- Auto interaction across several Monad ecosystems.
- Displays verified tokens held across all ecosystems on Monad.
- Supports proxy integration.
- Auto-funding from a primary account with sufficient MON balance.
- Configurable daily swap, ai craft voting and staking cycles.
- Colored UI and display.

## 🌐 Supported Ecosystems

- Monorail (DeX)
- AICraft.fun (AI)
- Kintsu (staking)
- Magma (staking)
- apriori (staking)

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
    "your_private_key1",
    "your_private_key2"
  ],
  "FUNDER_PRIVATE_KEY": "funding_wallet_private_key",
  "PROXIES": "http://user:pass@123.456.78.90:8080",
  "GITHUB_USERNAME": "",
  "FUND_AMOUNT": 0.5,
  "DAILY_SWAPS": 1,
  "DAILY_STAKES": 3,
  "DAILY_VOTES": 20
}
```

| **Setting**           | **Description**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| `PRIVATE_KEYS`         | List of private keys for the accounts you want to use.                          |
| `FUNDER_PRIVATE_KEY`   | Private key of the account that will fund other accounts with MON.              |
| `PROXIES`              | Proxy URL for anonymity. Format:<br>• Without auth: `http://ip:port`<br>• With auth: `http://user:pass@ip:port` |
| `GITHUB_USERNAME`      | Your GitHub username (used for starring the repo).                             |
| `FUND_AMOUNT`          | Amount of MON (in SOL or native token) to send per funding cycle.              |
| `DAILY_SWAPS`          | Number of swap transactions to perform daily.                                  |
| `DAILY_STAKES`         | Number of staking transactions to perform daily.                               |
| `DAILY_VOTES`          | Number of voting transactions to perform daily.                                |

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
