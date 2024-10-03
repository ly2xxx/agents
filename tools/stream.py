import requests
from bs4 import BeautifulSoup

# URL of the webpage to scrape
url = 'https://stream2watch.in/live/922-tv-'

# Send a GET request to the webpage
response = requests.get(url)

# Parse the HTML content
soup = BeautifulSoup(response.content, 'html.parser')

# Find video stream links (common formats)
video_links = []
for source in soup.find_all('source'):
    video_links.append(source.get('src'))

# Print the found video links
if video_links:
    print('Video stream links found:')
    for link in video_links:
        print(link)
else:
    print('No video stream links found.')