import asyncio
import json
import sys

import aiohttp
from bs4 import BeautifulSoup
from langchain.tools import tool
from pydantic import BaseModel, Field

# there is a known issue with the Python asyncio library on Windows specifically that happens when the Proactor event loop (the default on Windows) is closed while there are still outstanding tasks. It doesn’t affect the correct execution of the code, but something on Windows + aysncio + LangChain/LangGraph triggers it. 
# We’ll use the selector event loop policy to avoid this issue (this is only needed/triggers if you’re on Windows.).
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Multi-processing: is about spreading tasks over a computer’s CPU cores, and is well suited for tasks that require lots of mathematical computations.
# Multi-threading: is about running multiple threads in the same process, and is well suited for tasks that are I/O bound (like fetching webpages).
# Asynchronous programming: is a single-process, single-threaded design that uses coroutines to handle multiple tasks concurrently. Async functions are able to sort of pause and resume their execution, allowing other tasks to run in the meantime during this pause.
def parse_html(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in ["nav", "footer", "aside", "script", "style", "img", "header"]:
        for match in soup.find_all(tag):
            match.decompose()

    text_content = soup.get_text()
    text_content = " ".join(text_content.split())
    return text_content[:8_000]

async def get_webpage_content(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()

    text_content = parse_html(html_content)
    print(f"URL: {url} - fetched successfully.")
    return text_content

class ResearchInput(BaseModel):
    research_urls: list[str] = Field(description="Must be a list of valid URLs.")

@tool("research", args_schema=ResearchInput)
async def research(research_urls: list[str]) -> str:
    """Get content of provided URLs for research purposes."""
    tasks = [asyncio.create_task(get_webpage_content(url)) for url in research_urls]
    # The asyncio.create_task() function schedules the coroutine to run on the event loop and returns a Task object. 
    # *tasks is a way to unpack the list of tasks into separate arguments passing them into the function.
    # If return_exceptions is set to False, gather() will immediately raise the first exception it encounters. 
    # When set to True, instead of raising exceptions, it will return them in the result list so that contents will be a list of results or exceptions. 
    contents = await asyncio.gather(*tasks, return_exceptions=True)
    return json.dumps(contents)

if __name__ == "__main__":
    import time

    TEST_URLS = [
        "https://en.wikipedia.org/wiki/SpongeBob_SquarePants",
        "https://en.wikipedia.org/wiki/Stephen_Hillenburg",
        "https://en.wikipedia.org/wiki/The_SpongeBob_Movie:_Sponge_Out_of_Water",
    ]

    async def main():
        result = await research.ainvoke({"research_urls": TEST_URLS})

        with open("test.json", "w") as f:
            json.dump(result, f)
    # asyncio.run is a useful function that creates a new event loop, runs the given coroutine which is main in our case, closes the loop, and then returns the result. 
    # This makes it a convenient way to run async code from a synchronous context as it handles the whole event loop thing for us.
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"Async time: {end_time - start_time} seconds")