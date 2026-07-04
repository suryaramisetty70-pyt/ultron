"""
Ultron Creator Skills
Instant AI Image Generation using free pollinations.ai endpoint.
"""
import os
import requests
import urllib.parse
from datetime import datetime

def generate_image(prompt):
    """
    Generates an AI image from a text prompt and opens it on the screen.
    """
    print(f"[Creator Engine] Generating image for: {prompt}")
    try:
        # Format the prompt for the URL
        safe_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}"
        
        # Download the image
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Save to Desktop
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Ultron_Art_{timestamp}.jpg"
            filepath = os.path.join(desktop, filename)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
                
            # Automatically open the image
            os.startfile(filepath)
            
            return f"Successfully generated the image and saved it to the Desktop as {filename}. I have opened it on the screen."
        else:
            return f"Failed to generate image. Server returned status code: {response.status_code}"
            
    except Exception as e:
        return f"Image generation failed: {str(e)}"
