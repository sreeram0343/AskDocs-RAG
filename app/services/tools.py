import datetime
import logging
from llama_index.core.tools import FunctionTool

logger = logging.getLogger("askdocs-rag.services.tools")

def calculate_math(expression: str) -> str:
    """
    Safely evaluates basic mathematical expressions. 
    Use this for parsing or calculating statistics/numbers found in documents.
    """
    logger.info(f"External Math Tool triggered for expression: '{expression}'")
    try:
        # Define allowed math operations and characters for security
        allowed_chars = set("0123456789+-*/(). ")
        if not set(expression).issubset(allowed_chars):
            return "Error: Expression contains forbidden characters. Only numbers and basic operations (+ - * / ( ) .) are allowed."
            
        # Safe eval using limited globals
        allowed_names = {"__builtins__": None}
        result = eval(expression, allowed_names, {})
        return f"Result of math calculation '{expression}': {result}"
    except Exception as e:
        logger.error(f"Error in math calculator: {str(e)}")
        return f"Error evaluating math expression: {str(e)}"

def get_current_datetime() -> str:
    """
    Returns the current date and time.
    Use this to anchor any time-sensitive queries or temporal document comparisons.
    """
    now = datetime.datetime.now()
    logger.info(f"External Datetime Tool triggered. Current time: {now}")
    return f"Current system date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}"

# Wrap as LlamaIndex FunctionTools
math_tool = FunctionTool.from_defaults(
    fn=calculate_math,
    name="calculate_math",
    description="Evaluate basic mathematical expressions safely. Input should be a simple arithmetic string."
)

datetime_tool = FunctionTool.from_defaults(
    fn=get_current_datetime,
    name="get_current_datetime",
    description="Retrieve the current system date and time."
)

custom_tools = [math_tool, datetime_tool]
