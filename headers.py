import random


def get_random_user_agent():
    base_user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{webkit_version} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit_version}",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/{webkit_version} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit_version}",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/{webkit_version} (KHTML, like Gecko) Chrome/{chrome_version} Safari/{webkit_version}",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{webkit_version} (KHTML, like Gecko) Firefox/{firefox_version}",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:{firefox_version}) Gecko/20100101 Firefox/{firefox_version}",
    ]

    webkit_version = f"{random.randint(500, 600)}.{random.randint(0, 50)}"
    chrome_version = f"{random.randint(80, 100)}.0.{random.randint(4000, 5000)}.{random.randint(100, 150)}"
    firefox_version = f"{random.randint(80, 100)}.0"

    user_agent = random.choice(base_user_agents).format(
        webkit_version=webkit_version,
        chrome_version=chrome_version,
        firefox_version=firefox_version
    )

    return user_agent


def get_phantom_headers():
    return {
        "accept": "*/*",
        # "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "chrome-extension://bfnaelmomeimhlpmgjnjophhpkkoljpa",
        "priority": "u=1, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Microsoft Edge";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "none",
        "sec-fetch-storage-access": "active",
        "user-agent": get_random_user_agent(),
        "x-phantom-platform": "extension",
        "x-phantom-version": "25.9.1"
    }