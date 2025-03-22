import requests
import concurrent.futures
import random
import time


class ProxyTester:
    def __init__(self,
                 proxy_url='https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json'):
        """
        Initialize the ProxyTester with a proxy source URL

        :param proxy_url: URL to fetch proxies from
        """
        self.proxy_url = proxy_url
        self.proxies = []
        self.working_proxies = []

    def fetch_proxies(self):
        """
        Fetch proxies from the specified URL

        :return: List of proxy dictionaries
        """
        try:
            response = requests.get(self.proxy_url)
            data = response.json()
            self.proxies = data.get('proxies', [])
            print(f"Total proxies fetched: {len(self.proxies)}")
            return self.proxies
        except Exception as e:
            print(f"Error fetching proxies: {e}")
            return []

    def test_proxy(self, proxy_data, timeout=10):
        """
        Test a single proxy for connectivity and speed

        :param proxy_data: Dictionary containing proxy information
        :param timeout: Connection timeout in seconds
        :return: Tuple of (is_working, proxy_dict, response_time)
        """
        try:
            proxy_str = proxy_data.get('proxy', '')
            protocol = proxy_data.get('protocol', '')

            proxies = {
                'http': proxy_str,
                'https': proxy_str
            }

            start_time = time.time()
            response = requests.get('http://httpbin.org/ip',
                                    proxies=proxies,
                                    timeout=timeout)

            response_time = time.time() - start_time

            if response.status_code == 200:
                # print(f"Working proxy: {proxy_str} (Response time: {response_time:.2f}s)")
                return True, proxies, response_time
            return False, None, 0
        except Exception as e:
            return False, None, 0

    def test_proxies(self, max_workers=10, max_proxies=20):
        """
        Concurrently test proxies

        :param max_workers: Maximum number of concurrent proxy tests
        :param max_proxies: Maximum number of proxies to test
        :return: List of working proxies
        """
        self.working_proxies = []

        # Shuffle and limit proxies
        random.shuffle(self.proxies)
        proxies_to_test = self.proxies[:max_proxies]

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Use a list comprehension with executor.submit to test proxies
            futures = [executor.submit(self.test_proxy, proxy) for proxy in proxies_to_test]

            for future in concurrent.futures.as_completed(futures):
                is_working, proxy, response_time = future.result()
                if is_working:
                    self.working_proxies.append({
                        'proxy': proxy,
                        'response_time': response_time
                    })

        # Sort working proxies by response time
        self.working_proxies.sort(key=lambda x: x['response_time'])

        print(f"Total working proxies: {len(self.working_proxies)}")
        return self.working_proxies

    def make_request(self, url, proxy_index=0):
        """
        Make a GET request using a working proxy

        :param url: URL to request
        :param proxy_index: Index of the proxy to use from working_proxies
        :return: Response text or None
        """
        if not self.working_proxies:
            print("No working proxies available")
            return None

        try:
            proxy = self.working_proxies[proxy_index]['proxy']
            response = requests.get(url, proxies=proxy, timeout=10)
            return response.text
        except Exception as e:
            print(f"Request failed with proxy {proxy}: {e}")
            return None


def get_free_proxy():
    # Create a ProxyTester instance
    proxy_tester = ProxyTester()

    # Fetch proxies
    proxy_tester.fetch_proxies()

    # Test proxies
    print("Testing for working proxies...")
    proxy_tester.test_proxies(max_workers=20, max_proxies=50)

    # Example: Make a request using a proxy
    proxy_index = -1  # index starts at zero so set to -1
    if proxy_tester.working_proxies:
        for working_proxy in proxy_tester.working_proxies:
            proxy_index += 1
            response = proxy_tester.make_request('http://httpbin.org/ip', proxy_index)
            if response:
                # print("Successful request response:", response)
                return working_proxy


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
