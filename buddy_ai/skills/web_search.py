from duckduckgo_search import DDGS

def search_internet(query, max_results=3):
    """
    Perform a live web search using DuckDuckGo.
    Returns a formatted string of the top results.
    """
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No results found."
            
        formatted_results = []
        for r in results:
            formatted_results.append(f"Title: {r['title']}\nSnippet: {r['body']}")
            
        return "\n\n".join(formatted_results)
    except Exception as e:
        return f"Web search failed: {str(e)}"
