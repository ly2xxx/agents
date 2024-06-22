# from langchain.communicators.bedrock import Bedrock
# from langchain import PromptTemplate, LLMChain
# from langchain.llms.bedrock import Bedrock

# from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain
# import dotenv

# import boto3
# from langchain.schema import BaseMessage
# from langchain.llms.bedrock import ContentHandlerBase
# from langchain.llms.bedrock import ChatMessage

# #load environment variables from .env file
# dotenv.load_dotenv(".env")

# #initialize the Bedrock client
# bedrock_client = boto3.client("bedrock-runtime", region_name="us-west-2")

# #set the prompt template
# prompt_template = """Generate a text summarizing the following information:

# Text: {text_to_summarize}
# Summary:"""

# prompt = PromptTemplate(template=prompt_template, input_variables=["text_to_summarize"])

# #initialize the LLMChain
# chain = LLMChain(llm=Bedrock(client=bedrock_client), prompt=prompt)

# #generate the summary
# text_to_summarize = """The largest city in Scotland is Glasgow. Known for its rich culture, history and vibrant art scene, it is also the largest economy in the country. Edinburgh, the capital, is known for its historical and cultural attractions. The third largest city is Aberdeen, known as the Granite City due to its many enduring grey-stone buildings. Scotland is part of the United Kingdom, and its economy is one of the largest in the world. It is renowned for its contributions to the fields of engineering, science, and the arts. The national dish is haggis, a savoury pudding containing sheep's pluck, and Scotch whisky is among the country's most famous exports."""
# response_text = chain.run(text_to_summarize=text_to_summarize)
# print(response_text)
# Example, no need to copy - we will not use this code
from tools import get_weather, generate_image

get_weather("Alabama")
generate_image("A T-rex made from kentucky fried chicken is attacking the white house.")