#!/usr/bin/env python
# coding: utf-8

# In[1]:


from google.adk.agents import Agent, SequentialAgent, ParallelAgent, LoopAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool, FunctionTool, google_search
from google.genai import types

print("✅ ADK components imported successfully.")


# In[2]:


from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import load_memory, preload_memory
from google.genai import types

print("✅ ADK components imported successfully.")


# In[3]:


import uuid
from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from google.adk.apps.app import App, ResumabilityConfig
from google.adk.tools.function_tool import FunctionTool  # (not strictly needed here)


# In[44]:


from typing import Any, Dict

from google.adk.agents import Agent, LlmAgent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.models.google_llm import Gemini
from google.adk.sessions import DatabaseSessionService
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.tool_context import ToolContext
from google.genai import types

print("✅ ADK components imported successfully.")


# In[58]:


import json
import requests
import subprocess
import time
import uuid

from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import (
    RemoteA2aAgent,
    AGENT_CARD_WELL_KNOWN_PATH,
)

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Hide additional warnings in the notebook
import warnings

warnings.filterwarnings("ignore")

print("✅ ADK components imported successfully.")


# In[4]:


import os

try:
    GOOGLE_API_KEY = "AIzaSyCINWtb9Bm-W4wmTLb4uzz9NmYoyC00DiU"
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    print("✅ Setup and authentication complete.")
except Exception as e:
    print(
        f"🔑 Authentication Error: Please make sure you have added 'GOOGLE_API_KEY' to your Kaggle secrets. Details: {e}"
    )


# In[5]:


retry_config=types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1, # Initial delay before first retry (in seconds)
    http_status_codes=[429, 500, 503, 504] # Retry on these HTTP errors
)


# In[6]:


import requests
from typing import Optional

def project_gutenberg(title: str, author: Optional[str] = None):
    query = title if not author else f"{title} {author}"

    search_url = f"https://gutendex.com/books/?search={query}"
    res = requests.get(search_url).json()

    if res["count"] == 0:
        return {"error": f"No Project Gutenberg book found for {query}"}

    book = res["results"][0]

    # Select text format
    formats = book["formats"]
    text_url = (
        formats.get("text/plain; charset=utf-8") or
        formats.get("text/plain") or
        formats.get("text/html; charset=utf-8") or
        None
    )

    if not text_url:
        return {"metadata_only": book}

    # Fetch text (safe)
    text_res = requests.get(text_url)
    text_res.encoding = text_res.apparent_encoding
    full_text = text_res.text

    return {
        "metadata": {
            "title": book["title"],
            "authors": [a["name"] for a in book["authors"]],
            "subjects": book["subjects"],
            "gutenberg_id": book["id"],
            "download_count": book["download_count"]
        },
        "text_excerpt": full_text[:2500],  # enough for theme analysis
        "source_text_url": text_url,
        "api_source": "Gutendex"
    }


# In[7]:


import requests

def wikidata_query(sparql: str):
    """
    Run a SPARQL query on Wikidata and return JSON results.
    """
    url = "https://query.wikidata.org/sparql"
    
    headers = {
        "Accept": "application/sparql-results+json"
    }
    
    r = requests.get(url, params={"query": sparql}, headers=headers)

    if r.status_code != 200:
        return {"error": f"Wikidata query failed: {r.status_code}"}
    
    return r.json()


# In[8]:


# import requests
# from typing import Dict, Any

# def wikidata_query(sparql: str) -> Dict[str, Any]:
#     """
#     Run a SPARQL query on Wikidata and return the JSON result.

#     This is a low-level tool; other helper tools should build the SPARQL string
#     and pass it here.
#     """
#     url = "https://query.wikidata.org/sparql"
#     headers = {"Accept": "application/sparql-results+json"}
#     resp = requests.get(url, params={"query": sparql}, headers=headers)
#     resp.raise_for_status()
#     return resp.json()


# In[9]:


def literature_multi_search(query: str):
    """
    Unified search tool for literary metadata.
    Searches Wikipedia, Open Library, Goodreads (web-scrape fallback),
    and Google Books API.
    Returns combined hits with citations.
    """
    results = []

    # 1. Wikipedia summary API
    try:
        wiki = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        ).json()
        if "title" in wiki:
            results.append({
                "source": "Wikipedia",
                "title": wiki.get("title"),
                "extract": wiki.get("extract"),
                "url": f"https://en.wikipedia.org/wiki/{wiki.get('title').replace(' ', '_')}"
            })
    except:
        pass

    # 2. Open Library API
    try:
        ol = requests.get(f"https://openlibrary.org/search.json?title={query}").json()
        if ol['numFound'] > 0:
            doc = ol['docs'][0]
            results.append({
                "source": "OpenLibrary",
                "title": doc.get("title"),
                "author": doc.get("author_name", []),
                "first_publish_year": doc.get("first_publish_year"),
                "edition_key": doc.get("edition_key", []),
                "olid_url": f"https://openlibrary.org/works/{doc.get('key')}"
            })
    except:
        pass

    # 3. Google Books API
    try:
        gb = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": query, "maxResults": 2}
        ).json()
        if "items" in gb:
            for item in gb["items"]:
                info = item["volumeInfo"]
                results.append({
                    "source": "GoogleBooks",
                    "title": info.get("title"),
                    "authors": info.get("authors"),
                    "description": info.get("description"),
                    "publishedDate": info.get("publishedDate"),
                    "preview": info.get("previewLink"),
                })
    except:
        pass

    # 4. Goodreads (Non-API version, simple search scraping)
    try:
        gr_url = f"https://www.goodreads.com/search?q={query.replace(' ', '+')}"
        results.append({
            "source": "Goodreads",
            "search_url": gr_url,
            "note": "Goodreads no longer has a public API. This returns a search URL."
        })
    except:
        pass

    return {"query": query, "results": results}


# In[10]:


async def run_session(
    runner_instance: Runner, user_queries: list[str] | str, session_id: str = "default"
):
    """Helper function to run queries in a session and display responses."""
    print(f"\n### Session: {session_id}")

    # Create or retrieve session
    try:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
    except:
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )

    # Convert single query to list
    if isinstance(user_queries, str):
        user_queries = [user_queries]

    # Process each query
    for query in user_queries:
        print(f"\nUser > {query}")
        query_content = types.Content(role="user", parts=[types.Part(text=query)])

        # Stream agent response
        async for event in runner_instance.run_async(
            user_id=USER_ID, session_id=session.id, new_message=query_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                text = event.content.parts[0].text
                if text and text != "None":
                    print(f"Model: > {text}")


print("✅ Helper functions defined.")


# In[11]:


memory_service = (
    InMemoryMemoryService()
)  # ADK's built-in Memory Service for development and testing


# In[12]:


# Define constants used throughout the notebook
APP_NAME = "MemoryDemoApp"
USER_ID = "demo_user"


# In[13]:


async def auto_save_to_memory(callback_context):
    """Automatically save session to memory after each agent turn."""
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session
    )


print("✅ Callback created.")


# In[ ]:





# In[15]:


### History Agent


# In[16]:


# from typing import Dict, Any, List

# # Optional: simple mapping from human term → Wikidata QID
# TOPIC_QIDS = {
#     "French Revolution": "Q178546",
#     "German Revolution of 1918–1919": "Q1510464",
#     # add more as needed
# }

# def wikidata_events_for_topic(topic_label: str) -> Dict[str, Any]:
#     """
#     Given a known topic label (e.g. 'French Revolution'),
#     run a SPARQL query that returns related historical events with dates.
#     """
#     qid = TOPIC_QIDS.get(topic_label)
#     if not qid:
#         return {"error": f"No QID mapping for topic '{topic_label}'."}

#     sparql = f"""
#     SELECT ?event ?eventLabel ?date WHERE {{
#       /* restrict to historical events */
#       ?event wdt:P31/wdt:P279* wd:Q1190554;

#       /* main subject = {topic_label} */
#       ?event wdt:P921 wd:{qid};

#       /* point in time */
#       ?event wdt:P585 ?date.

#       SERVICE wikibase:label {{
#         bd:serviceParam wikibase:language "en".
#       }}
#     }}
#     ORDER BY ?date
#     """

#     return wikidata_query(sparql)


# In[17]:


# COUNTRY_QIDS = {
#     "Germany": "Q183",
#     "France": "Q142",
#     # add as needed
# }

# def wikidata_events_for_country_period(
#     country_label: str,
#     start_date: str,
#     end_date: str
# ) -> Dict[str, Any]:
#     """
#     Return historical events in a given country between start_date and end_date.
#     Dates should be 'YYYY-MM-DD'.
#     """
#     qid = COUNTRY_QIDS.get(country_label)
#     if not qid:
#         return {"error": f"No QID mapping for country '{country_label}'."}

#     sparql = f"""
#     SELECT ?event ?eventLabel ?date WHERE {{
#       /* historical event class */
#       ?event wdt:P31/wdt:P279* wd:Q1190554;

#       /* country = {country_label} */
#       ?event wdt:P17 wd:{qid};

#       /* event date */
#       ?event wdt:P585 ?date.

#       /* timeframe filter */
#       FILTER (
#         ?date >= "{start_date}T00:00:00Z"^^xsd:dateTime &&
#         ?date <= "{end_date}T00:00:00Z"^^xsd:dateTime
#       )

#       SERVICE wikibase:label {{
#         bd:serviceParam wikibase:language "en".
#       }}
#     }}
#     ORDER BY ?date
#     """

#     return wikidata_query(sparql)


# In[18]:


# import requests

# def history_multi_search(query: str):
#     """
#     Unified historical search:
#     - Wikipedia summary (main entry)
#     - Maybe related page for 'History of X'
#     - Google Books as backup for history overviews
#     """
#     results = []

#     # 1. Wikipedia main page
#     try:
#         wiki = requests.get(
#             f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
#         ).json()
#         if "title" in wiki:
#             results.append({
#                 "source": "Wikipedia",
#                 "title": wiki.get("title"),
#                 "extract": wiki.get("extract"),
#                 "url": f"https://en.wikipedia.org/wiki/{wiki.get('title').replace(' ', '_')}"
#             })
#     except Exception:
#         pass

#     # 2. Maybe a "History of X" page
#     try:
#         hist_title = f"History of {query}"
#         wiki_hist = requests.get(
#             f"https://en.wikipedia.org/api/rest_v1/page/summary/{hist_title.replace(' ', '_')}"
#         ).json()
#         if "title" in wiki_hist and wiki_hist.get("title").startswith("History of"):
#             results.append({
#                 "source": "Wikipedia",
#                 "title": wiki_hist.get("title"),
#                 "extract": wiki_hist.get("extract"),
#                 "url": f"https://en.wikipedia.org/wiki/{wiki_hist.get('title').replace(' ', '_')}"
#             })
#     except Exception:
#         pass

#     # 3. Google Books (history overviews)
#     try:
#         gb = requests.get(
#             "https://www.googleapis.com/books/v1/volumes",
#             params={"q": f"{query} history", "maxResults": 2}
#         ).json()
#         if "items" in gb:
#             for item in gb["items"]:
#                 info = item["volumeInfo"]
#                 results.append({
#                     "source": "GoogleBooks",
#                     "title": info.get("title"),
#                     "authors": info.get("authors"),
#                     "description": info.get("description"),
#                     "publishedDate": info.get("publishedDate"),
#                     "preview": info.get("previewLink"),
#                 })
#     except Exception:
#         pass

#     return {"query": query, "results": results}


# In[19]:


# history_agent = Agent(
#     name="HistoryAgent",
#     model=Gemini(
#         model="gemini-2.5-flash-lite",
#         retry_options=retry_config,
#     ),
#     instruction="""
# You are a Historical Context and Timeline Agent.

# Tools you can use:
# - history_multi_search(query: str): gives you Wikipedia-style summaries and book metadata.
# - wikidata_events_for_topic(topic_label: str): returns JSON with bindings of ?event, ?eventLabel, ?date.
# - wikidata_events_for_country_period(country_label: str, start_date: str, end_date: str):
#   returns JSON of events in that country and period.

# Your job:

# 1. From the user's request, decide what they are asking about:
#    - a specific historical topic (e.g. "French Revolution"),
#    - or a country and period (e.g. "Germany 1871–1918"),
#    - or something literary that implicitly refers to a context (e.g. "background for Hyperion").

# 2. Use the tools to gather facts:
#    - For big named events (e.g. French Revolution), try wikidata_events_for_topic("<label>").
#    - For country-period questions, use wikidata_events_for_country_period("<country>", "<start>", "<end>").
#    - Use history_multi_search() to get narrative summaries.

# 3. Parse the JSON you get back:
#    - Look into the 'results'/'bindings' field.
#    - Extract the event label and date from each row.
#    - Choose the 5–10 most relevant events.

# 4. Write a human-readable answer in natural language:
#    - Title / Topic
#    - Timeline: bullet list "YYYY: short description"
#    - Socio-Political Context: 1–3 paragraphs
#    - Why this matters for the user's topic.

# IMPORTANT:
# - Do NOT output JSON or code. Only natural language.
# - If tools give you little or nothing, fall back to your general historical knowledge
#   and say that some details are based on general knowledge.

# """,
#     tools=[
#         history_multi_search,
#         wikidata_events_for_topic,
#         wikidata_events_for_country_period,
#     ],
#     output_key="historical_context_text",
# )

# print("✅ history_agent wired with SPARQL-based tools.")


# In[ ]:





# ## Start Agent Architecture

# In[20]:


literature_agent = Agent(
    name="LiteratureAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config,
    ),
    instruction="""
You are a Literature Guide and Critic.

Your job:
1. Use the available tools (literature_multi_search, wikidata_query, project_gutenberg)
   to gather information about a literary work: title, author, publication era, movement,
   short summary, main themes, and any notable quotes or influences.
2. Then write a clear, well-structured explanation in natural language,
   as if you are talking to a curious, non-expert reader.

Output format (very important):
- Do NOT return JSON, Python dictionaries, or any machine-readable structures.
- Do NOT wrap your answer in backticks or code blocks.
- Instead, respond as flowing natural language with light structure, for example:

  Title and Context:
  - Briefly identify the work (title, author, era, movement).

  Summary:
  - 1–2 short paragraphs summarizing the work.

  Themes and Motifs:
  - Bullet points or short paragraphs explaining the key themes.

  Why It Matters:
  - A brief reflection on the work’s significance or how it connects to other classics.

Citations:
- At the end, briefly mention which tools/sources you relied on (e.g. “Based on data from Wikipedia, Open Library, and Project Gutenberg”),
  in plain language.
""",
    tools=[literature_multi_search, wikidata_query, project_gutenberg],
    # This key just labels what we store; the content itself is plain text.
    output_key="literary_analysis",
)

print("✅ literature_agent updated for natural-language output.")


# In[21]:


# runner = InMemoryRunner(agent=literature_agent)
# response = await runner.run_debug(
#     "Please analyze 'Hyperion' by Friedrich Hölderlin."
# )
# response


# In[22]:


history_agent = Agent(
    name="HistoryAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config,
    ),
    instruction="""
You are a Historical Context Agent.

The user will give you the title and (optionally) author of a literary work
(e.g. "Hyperion by Friedrich Hölderlin").

Your job:
1. Use the tools to infer:
   - the time period when the work was written/published,
   - major historical events, cultural movements, or intellectual currents
     relevant to the work and its author,
   - how these historical forces shaped the themes or tone of the work.
2. Write a concise explanation in natural language (up to 3–6 paragraphs).

Output:
- Natural language prose only (no JSON, no code fences).
- Use headings if helpful (e.g. "Historical Background", "Intellectual Climate").

Your answer will be stored as the historical context for this work.
""",
    tools=[google_search],
    output_key="historical_context",
)

print("✅ history_agent created.")


# In[23]:


# runner = InMemoryRunner(agent=history_agent)
# response = await runner.run_debug(
#     "Please analyze 'Hyperion' by Friedrich Hölderlin."
# )
# response


# In[24]:


cultural_linker_agent = Agent(
    name="CulturalLinkerAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config,
    ),
    instruction="""
You are a Cultural Linker and Curator.

For each call, the user message you receive will contain:
- a section starting with "LITERARY ANALYSIS:"
- a section starting with "HISTORICAL CONTEXT:"

Your job:
1. Carefully read both sections.
2. Based on them, suggest related cultural works:
   - other books or authors,
   - films or TV series,
   - music (composers, pieces, albums),
   - visual art or photography,
   - optionally relevant philosophical texts or essays.
3. For each recommendation, briefly explain WHY it resonates with the original work
   (shared themes, mood, historical concerns, etc.).

Output format:
- Natural language prose only (no JSON, no code fences).
- You may use headings like:
  - "Related Literature"
  - "Film / Television"
  - "Music"
  - "Visual Art"
  - "Philosophy / Essays"

Your answer will be stored as the cultural links for this work.
""",
    tools=[literature_multi_search, wikidata_query],
    output_key="cultural_links",
)

print("✅ cultural_linker_agent created.")


# In[25]:


archivist_agent = LlmAgent(
    name="ArchivistAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config,
    ),
    instruction="""
You are the Archivist in a cultural multi-agent system. You will combine these three cultural findings into a singles cultural atlas entry:


    **LITERARY ANALYSIS:**
    {literary_analysis}
    
    **HISTORICAL CONTEXT:**
    {historical_context}
    
    **CULTURAL LINKS:**
    {cultural_links}

Your job:
- Read all three sections.
- Synthesize them into a single, coherent “Cultural Atlas Entry” for the work.
- Write in clear, engaging natural language for a curious non-expert reader.
- The final summary should be around 1000 words.


Output format:
- Natural language prose only (no JSON, no code).
- Suggested structure:
  1. Title and Coordinates (work, author, era, movement)
  2. What the Work Is About (summary)
  3. Themes and Questions (drawing on the analysis and context)
  4. Cultural Constellation (integrating the cultural links)
  5. Suggested Next Steps (how the user might continue exploring)

Do not mention internal agents or tools; just present the atlas entry as a polished explanation.  Your summary should highlight common themes, surprising connections, and the most important key takeaways from all three reports. The final summary should be around 200 words.

Your answer will be the final cultural atlas entry.
""",
    output_key="cultural_atlas_entry",
)

print("✅ archivist_agent created.")



# In[34]:


# The ParallelAgent runs all its sub-agents simultaneously.
parallel_research_team = ParallelAgent(
    name="ParallelResearchTeam",
    sub_agents=[literature_agent, history_agent, cultural_linker_agent],
)

# This SequentialAgent defines the high-level workflow: run the parallel team first, then run the aggregator.
sequence_agent = SequentialAgent(
    name="CulturalAtlasCoordinator",
    sub_agents=[parallel_research_team, archivist_agent],
)

print("✅ Sequential Agents created.")


## Add memory

cultural_atlas_tool = AgentTool(sequence_agent)


# In[36]:


root_agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    name="AtlasWithMemory",
    instruction="""
You are the entrypoint for the user's Cultural Atlas queries.

The system may automatically provide you with past conversation snippets
under a special <PAST_CONVERSATIONS> tag. Use that context if it is present.

You have one callable tool:
- CulturalAtlasGraph: given a user request about a work, it runs the full
  multi-agent pipeline (literature, history, cultural links, archivist)
  and returns a cultural atlas entry.

Workflow YOU MUST follow for each user request:
1. Read any <PAST_CONVERSATIONS> context if present and keep it in mind.
2. Call the CulturalAtlasGraph tool with the user's query
   (e.g. "Please create a cultural atlas entry for 'The Bell Jar' by Sylvia Plath.").
3. Return the cultural atlas entry from CulturalAtlasGraph as your answer.
   Do not mention tools or memory internals; just present the result.

After each turn, your session will be saved to long-term memory automatically
(via the callback).
""",
    tools=[preload_memory, cultural_atlas_tool],  # preload_memory stays here
    after_agent_callback=auto_save_to_memory,
)

















