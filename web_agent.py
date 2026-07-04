import requests

def search_web(query):

    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json"

        response = requests.get(url)
        data = response.json()

        results = []

        if data.get("AbstractText"):
            results.append(data["AbstractText"])

        for topic in data.get("RelatedTopics", []):
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(topic["Text"])

        if results:
            return results[:3]

        return ["No useful results found."]

    except:
        return ["Error fetching data."]