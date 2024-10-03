import requests
from bs4 import BeautifulSoup
import time
import random


def get_discounted_items(search_term):
    url = f'https://www.amazon.co.uk/s?k={search_term}&i=warehouse-deals'
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.6 Mobile/15E148 Safari/604.1',
    ]
    items = []

    for attempt in range(5):  # Retry up to 5 times
        headers = {'User-Agent': random.choice(user_agents)}
        response = requests.get(url, headers=headers)
        print(f'Status Code: {response.status_code}')  # Print status code
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            print(soup.prettify())  # Print the HTML content for debugging
            for item in soup.find_all('div', {'data-component-type': 's-search-result'}):
                try:
                    new_price = item.find('span', 'a-price a-text-price').find('span', 'a-offscreen').text
                    used_price = item.find('span', 'a-price a-text-price a-size-medium').find('span', 'a-offscreen').text
                    new_price_value = float(new_price.replace('£', '').replace(',', '').strip())
                    used_price_value = float(used_price.replace('£', '').replace(',', '').strip())

                    if used_price_value <= new_price_value * 0.5:
                        item_url = 'https://www.amazon.co.uk' + item.h2.a['href']
                        items.append(item_url)
                except Exception as e:
                    continue
            break  # Exit loop if successful
        else:
            time.sleep(random.randint(2, 5))  # Wait for a random time between 2 to 5 seconds before retrying

    return items

# Example usage
search_term = 'golf'
print(get_discounted_items(search_term))

# pip install requests beautifulsoup4

# Agent 0: Responding:
# To access product data from Amazon, you can use the Amazon Product Advertising API. Here are the steps to get started:

# 1. **Create an Amazon Associate Account**: You need to sign up for an Amazon Associate account to access the Product Advertising API.

# 2. **Generate Access and Secret Keys**: After creating your account, you will need to generate an access key and a secret key. This is done in the Amazon Associates dashboard.

# 3. **Use the API**: With the keys, you can make requests to the API to retrieve product details. You can use operations like ItemLookup or ItemSearch to get the information you need.

# 4. **Refer to Documentation**: For detailed instructions and examples, refer to the following resources:
#    - [How to Use Amazon Product API - DEV Community](https://dev.to/cyanspray/how-to-use-amazon-product-api-igk)
#    - [API To Get Products Details From Amazon - Medium](https://medium.com/@aleb/api-to-get-products-details-from-amazon-58e5511a3a3a)
#    - [How to use Amazon API: examples and pricing [2024] - Elfsight](https://elfsight.com/blog/how-to-use-amazon-ecommerce-api-examples-and-pricing/)
#    - [How to Get Product Details from the Amazon API | Algopix](https://algopix.com/blog/how-to-get-product-details-from-the-amazon-api)
#    - [Getting complete product information using Amazon Product API - Stack Overflow](https://stackoverflow.com/questions/77855412/getting-complete-product-information-using-amazon-product-api)

# By following these steps, you can effectively access and utilize Amazon's product data.