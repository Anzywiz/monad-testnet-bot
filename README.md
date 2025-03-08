# Monad Farming Bot

If you're farming the Monad and want to automate interactions across multiple accounts programmatically, this bot is for you. It supports auto-farming, multiple account management, and proxy integration to enhance efficiency and anonymity.

## 🚀 Features

- Automates farming across multiple accounts.
- Auto-funding from a primary account with sufficient MON balance.
- Configurable daily swap cycles.
- Supports both personal and free proxy integration.



## 📌 Setup

Follow these steps to set up and run the bot.

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Anzywiz/monad-testnet-bot.git
cd monad-testnet-bot
```

### 2️⃣ Create and Activate a Virtual Environment

#### Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux/Mac:

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
  "private_keys": ["your_private_key1", "your_private_key2"],
  "funder_private_key": "your_funder_private_key",
  "fund_amount": 0.5,
  "daily_swap_cycles": 5,
  "proxies": "https://username:password@proxy_address:port",
  "github_username": "your_github_username"
}
```

- Replace `your_private_key1`, `your_private_key2` with actual private keys of the accounts you want to farm with.
- Set `funder_private_key` to the account that will fund your other accounts with MON.
- `fund_amount` is the amount of MON to send per funding cycle.
- `daily_swap_cycles` determines how many swaps will be executed daily.
- `proxies` can be set to a valid proxy URL or `null` if you do not have one.
- `github_username` must be your GitHub username (starring the repo is required).

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

⭐ **Don't forget to star the repo if you find it useful! Your support helps keep the project growing!** 😊

