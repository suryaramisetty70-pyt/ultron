"""
Ultron Document Reader (Gemini Parity)
Parses and summarizes massive PDF and text documents.
"""
import os
import PyPDF2

def read_large_document(filepath):
    """
    Reads a large document (PDF or TXT) and returns its contents.
    This simulates a massive context window by allowing the AI to read entire books.
    """
    try:
        if not os.path.exists(filepath):
            return f"Error: The file '{filepath}' does not exist."
            
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.pdf':
            text = f"--- PDF DOCUMENT: {filepath} ---\n"
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                total_pages = len(reader.pages)
                
                # To prevent overloading context limit initially, we read up to 50 pages.
                pages_to_read = min(total_pages, 50)
                for i in range(pages_to_read):
                    page = reader.pages[i]
                    text += f"\n[Page {i+1}]\n" + page.extract_text()
                    
                if total_pages > 50:
                    text += f"\n... (Document truncated. {total_pages - 50} pages remaining) ..."
                    
            return text
            
        elif ext in ['.txt', '.md', '.csv', '.json', '.py', '.js', '.html']:
            # Fallback to standard text reading for other formats
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"--- TEXT DOCUMENT: {filepath} ---\n{content}"
            
        else:
            return f"Error: Unsupported file format '{ext}'. I can currently read PDF and text files."
            
    except Exception as e:
        return f"Failed to read document {filepath}: {str(e)}"
