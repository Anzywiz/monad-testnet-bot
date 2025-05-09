# Monad Interaction Bot

If you're farming the Monad testnet and want to automate interactions across multiple dApps, this bot is for you. It supports daily interactions, staking, voting, NFT minting and more on key Monad ecosystem protocols. The bot integrates proxy support, and enables selective dApp interaction through a flexible configuration.

## 🚀 Features

* Auto interaction across selected Monad dApps.
* Supports daily voting, staking, and swapping.
* Proxy integration (including free proxies).
* Auto-funding accounts with low MON balances.
* Filter accounts to farm using `PRIVATE_KEYS_RANGE`.
* Customize interaction frequency per dApp.
* Clean colored UI for enhanced visibility.

## 🌐 Supported Ecosystems (from `SCRIPTS`)

* **Ambient** – Swap on Ambient.
* **AICraft.fun** – Login/create account using referral and vote based on random countries.
* **Apriori** – Stake/unstake MON tokens.
* **Bean** – Perform daily swaps.
* **Bebop** – Perform daily swaps.
* **Izumi** – Perform daily swaps.
* **Kintsu** – Stake/unstake MON tokens.
* **LilChogsters** – Interact and Mint on the NFT platform.
* **Magma** – Stake/unstake MON tokens.
* **Monorail** – Use Monorail's API for token swaps.
* **Rubic** – Perform daily swaps.
* **Uniswap** – Perform daily swaps.
* **Zona Finance** – Random daily betting with 1-hour duration: [https://app.zona.finance/](https://app.zona.finance/)

## 📌 Setup

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

### 4️⃣ Add Your Private Keys

Create a `private_keys.txt` file in the base directory. Place one private key per line for each account you want to farm.

### 5️⃣ Configure the Bot

Create a `config.json` file in the project root with the following structure:

```json
{
  "SCRIPTS": ["monorail", "stakers", "aicraft", "ambient", "bean", "bebop", "izumi", "lilchogsters", "rubic", "uniswap", "zona"],
  "PRIVATE_KEYS_RANGE": [1, 2],
  "FUNDER_PRIVATE_KEY": "your funding account pk",
  "FUND_AMOUNT": 0.5,
  "PROXIES": "",
  "GITHUB_USERNAME": "your github username",
  "STAKERS": ["magma", "apriori", "kintsu"],
  "AICRAFT": {
    "dailyVotes": 20,
    "referralCode": null,
    "countryCodeToVote": ["IN", "US", "ID", "PK", "NG", "BR"]
  },
  "DAILY_INTERACTION": {
    "DEX": {
      "ambient": 1,
      "bean": 1,
      "bebop": 1,
      "izumi": 1,
      "monorail": 1,
      "rubic": 1,
      "uniswap": 1
    },
    "STAKERS": 1
  }
}
```

### 🔍 Config Description Table

| **Setting**                 | **Description**                                                                         |
| --------------------------- | --------------------------------------------------------------------------------------- |
| `SCRIPTS`                   | List of dApps to interact with. Remove any dApp to skip interaction with it.            |
| `private_keys.txt`          | File containing private keys. One key per line.                                         |
| `PRIVATE_KEYS_RANGE`        | Index range (1-based) of keys from `private_keys.txt` to use. Leave blank to use all.   |
| `FUNDER_PRIVATE_KEY`        | Private key for the funding wallet.                                                     |
| `FUND_AMOUNT`               | Amount of MON to send to low-balance accounts.                                          |
| `PROXIES`                   | Proxy URL (leave blank for no proxy). Supports auth and free proxies.                   |
| `GITHUB_USERNAME`           | Used for starring the repo.                                                             |
| `STAKERS`                   | List of staking dApps to interact with. Remove items or the whole list to skip staking. |
| `AICRAFT.dailyVotes`        | Number of votes to cast daily on AICraft. Max is 20.                                               |
| `AICRAFT.referralCode`      | Referral code to use for new AICraft account registrations.                             |
| `AICRAFT.countryCodeToVote` | List of country codes to vote for.                                                      |
| `DAILY_INTERACTION.DEX`     | Dict of DEX dApps with number of daily swaps per DEX.                                   |
| `DAILY_INTERACTION.STAKERS` | Number of staking/unstaking actions to perform daily.                                   |

### 6️⃣ Run the Bot

```bash
python main.py
```

## 🔄 Updates

```bash
git pull
```

Check regularly for the latest features and fixes.

## 🛠 Issues & Contributions

* Encounter a bug? Report it in the Issues section.
* Want to contribute? Fork the repo, make changes, and submit a pull request.

## 📜 License

This project is licensed under the MIT License.

## 🤔 Why This Bot?

Many existing Monad scripts produce fake or unverifiable interactions. This bot ensures your activities across dApps are legitimate and recorded on-chain, boosting your eligibility in testnet evaluations.

⭐ If you find this helpful, please star the repo!
