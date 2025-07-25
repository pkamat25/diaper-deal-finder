"""
AutoGen Diaper Deal Finder
Automated diaper deal search using AutoGen and LangChain
"""
import asyncio
from io import BytesIO
import requests
import os
from autogen_agentchat.messages import TextMessage, MultiModalMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from dotenv import load_dotenv
# LangChain tool integration
from autogen_ext.tools.langchain import LangChainToolAdapter
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain.agents import Tool

# Load environment variables
load_dotenv(override=True)

async def main():
    """Main function to run diaper deal search"""
    
    prompt = """Your task is to find REAL DISCOUNTS and SPECIALS on Size 3 baby nappies from Australian supermarkets Coles and Woolworths.
🇦🇺 AUSTRALIAN SEARCH STRATEGY:
STEP 1 - SEARCH COLES SPECIALS:
Search these exact terms:
- "site:coles.com.au baby nappies size 3 special"
- "Coles catalogue baby nappies half price"
- "Coles Down Down baby nappies specials"
Look for: Red "Special" tags, Yellow "Down Down" pricing, "Was $X Now $Y"
STEP 2 - SEARCH WOOLWORTHS SPECIALS:
Search these exact terms:
- "site:woolworths.com.au baby nappies size 3 special"  
- "Woolworths catalogue baby nappies low price"
- "Woolworths baby nappies % off discount"
Look for: Red "Special" badges, Orange "Low Price" tags, Crossed-out prices
⚠️ CRITICAL VALIDATION:
- ONLY include products with CLEAR DISCOUNTS
- Original price MUST BE HIGHER than current price
- If prices same = NOT A DEAL
- Look for "Special", "Half Price", "% off", "Save $" badges
STEP 2: Write all findings to a file called diaper_everyday_deals.md with these details clear table format: 
- Supermarket name
- Diaper brand and product Type
- Regular price
- Offer Price / Discounted Price  
- Pack size and price per diaper
STEP 3: **Highlight Best Deals**: Clearly indicate which brand and store offers the best value. For example, mention the lowest price per nappy followed by the supermarket where it's available.
Reply with a short summary of the selected deal, only after saving all deals to the file.
#CRITICAL: After searching, use the write_file tool to save results to diaper_everyday_deals.md
IMPORTANT: In your final response, do NOT include any FunctionCall details or raw search results. Only provide the clean, formatted summary."""

    # Setup tools 
    serper = GoogleSerperAPIWrapper()
    langchain_serper = Tool(name="internet_search", func=serper.run, description="useful for when you need to search the internet")
    autogen_serper = LangChainToolAdapter(langchain_serper)
    autogen_tools = [autogen_serper]
    
    # Add LangChain file management tools
    langchain_file_management_tools = FileManagementToolkit(root_dir="/home/runner/work/diaper-deal-finder/diaper-deal-finder/artifacts").get_tools()
    for tool in langchain_file_management_tools:
        autogen_tools.append(LangChainToolAdapter(tool))
   
    # Print available tools 
    print(f"Available tools ({len(autogen_tools)}):")
    for tool in autogen_tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Setup agent 
    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
    agent = AssistantAgent(name="searcher", model_client=model_client, tools=autogen_tools, reflect_on_tool_use=True)
    
    # Run the search 
    message = TextMessage(content=prompt, source="user")
    result = await agent.on_messages([message], cancellation_token=CancellationToken())
    
    # Print results
    for message in result.inner_messages:
        print(message.content)
   
    # Check if file was created
    if not os.path.exists("./artifacts/diaper_everyday_deals.md"):
        print("❌ File creation failed - checking console for errors")
    else:
        print("✅ diaper_everyday_deals.md created successfully")
    
    # Send email 
    try:
        from email_sender import send_diaper_deals
        send_diaper_deals()
    except Exception as e:
        print(f"Email error: {e}")

# FIXED: Was **name** now __name__
if __name__ == "__main__":
    asyncio.run(main())
