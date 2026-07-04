"""
Ultron Research Skills
Handles live web search and Wikipedia lookups.
"""
from duckduckgo_search import DDGS
import wikipedia

def search_web(query, max_results=3):
    """
    Searches the live internet for up-to-date information.
    """
    print(f"[Research Agent] Searching web for: {query}")
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"Title: {r['title']}\nSummary: {r['body']}\nLink: {r['href']}")
        if not results:
            return "No results found on the web."
        return "\n\n".join(results)
    except Exception as e:
        return f"Web search failed: {str(e)}"

def search_wikipedia(query):
    """
    Searches Wikipedia for factual, encyclopedic summaries.
    """
    print(f"[Research Agent] Searching Wikipedia for: {query}")
    try:
        return wikipedia.summary(query, sentences=4)
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Query is too broad. Options: {e.options[:5]}"
    except wikipedia.exceptions.PageError:
        return "No Wikipedia page found for that query."
    except Exception as e:
        return f"Wikipedia search failed: {str(e)}"
