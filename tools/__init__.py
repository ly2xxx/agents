from .image import generate_image
from .weather import get_weather
from .pdf import markdown_to_pdf_file
from .rag import rag_query
# This will import the generate_image and get_weather tools from their respective files and make them available when importing the tools folder. It has effectively made the tools folder a package that can be imported from as a single entity.

# Define __all__ to control what is imported with 'from mypackage import *'
__all__ = ['generate_image', 'markdown_to_pdf_file', 'rag_query']