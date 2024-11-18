import os
import json
import string
import numpy as np
import tkinter as tk
from tkinter import ttk
from openai import OpenAI
import pymupdf

# Setup and initialization
Api_key = os.getenv('Open_AI_API_Key')
client = OpenAI(api_key=Api_key)
message = ""
manual_path = 'selected_manual.json'
pages = []
texts = []

# Tkinter GUI setup
root = tk.Tk()
root.title("Operational Manual Navigation Interface")
root.geometry("600x400")
root.minsize(600, 300)

# Padding value for consistent spacing
PADDING = 10

# Configure grid layout
root.columnconfigure(0, weight=1)  # Console column expands fully
root.columnconfigure(1, weight=0)  # Button column has a fixed size
root.rowconfigure(0, weight=1)     # Console row expands vertically

# Left Panel: Console
console_text = tk.Text(root, wrap=tk.WORD, state="normal", bg="black", fg="green")
console_text.grid(row=0, column=0, sticky="nsew", padx=PADDING, pady=PADDING)

# Add monospace text
banner_text = """
   ____        __  __       _   _       _____     
  / __ \\      |  \\/  |     | \\ | |     |_   _|    
 | |  | |     | \\  / |     |  \\| |       | |      
 | |  | |     | |\\/| |     | . ` |       | |      
 | |__| |  _  | |  | |  _  | |\\  |  _   _| |_   _ 
  \\____/  (_) |_|  |_| (_) |_| \\_| (_) |_____| (_)
                                                   
                                                  

     Operational Manual Navigation Interface...
"""

console_text.insert(tk.END, banner_text)
console_text.yview(tk.END)
console_text.config(state="disabled")

# Right Panel: Buttons
button_frame = ttk.Frame(root, width=120)
button_frame.grid(row=0, column=1, sticky="nsew", padx=PADDING, pady=PADDING)
button_frame.grid_propagate(False)
button_frame.rowconfigure(0, weight=1)  # Push buttons to the bottom
button_frame.rowconfigure(1, weight=0)  # Open Page button
button_frame.rowconfigure(2, weight=0)  # Search button

# Open Page button
open_page_button = tk.Button(button_frame, text="Open Page", relief="solid", borderwidth=1, highlightthickness=0, width=15, height=3, anchor="center")
open_page_button.grid(row=1, column=0, pady=5)

# Search button
search_button = tk.Button(button_frame, text="Search", relief="solid", borderwidth=1, highlightthickness=0, width=15, height=3, anchor="center")
search_button.grid(row=2, column=0, pady=5)

# Query Input below the console
query_entry = ttk.Entry(root)
query_entry.grid(row=1, column=0, columnspan=1, sticky="ew", padx=PADDING, pady=(0, PADDING))

# Define the function to get the query embedding from OpenAI
def get_query_embedding(user_query):
    """Create embedding for the user query."""
    user_query = "Summarize the following problem into a short string that highlights the topics relevant to the issue: " + user_query
    query_summary = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a Space Shuttle technical manual."},
            {"role": "user", "content": user_query}
        ]
    )
    message = query_summary.choices[0].message.content
    console_text.config(state="normal")
    console_text.insert(tk.END, f"Query Summary: {message}\n\n")
    console_text.yview(tk.END)
    console_text.config(state="disabled")
    
    # Create the embedding from the summary
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=message,
        encoding_format="float"
    )
    return response.data[0].embedding

# Find the closest page from the manual based on embedding
def find_closest_page(query_embedding, manual_path):
    """Find the closest page in the selected manual."""
    with open(manual_path, 'r') as f:
        manual_data = json.load(f)
    
    max_similarity = -1
    best_match = None

    for content in manual_data:
        with open(content, 'r') as f:
            manual_data = json.load(f)
        for data in manual_data:  # Assuming content is a list of dictionaries
            page_embedding = np.array(data['Data'])
            similarity = np.dot(query_embedding, page_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(page_embedding))

            if similarity > max_similarity:
                max_similarity = similarity
                best_match = {'filepath': data['filepath'], 'page': data['page']}
                print(best_match)
                pages.append(best_match)

# Get the page info from the closest page
def get_page_info(pages):
    print(f"Found {len(pages)} matching pages.")
    for i in range(min(3, len(pages))):
        page = pages[-i-1]  # Get the most recent page
        doc = pymupdf.open(page['filepath'])
        pg = doc[page['page']]
        text = pg.get_text("text")
        text = text.replace("\n", " ")
        texts.append(text)

# Final query to summarize the result based on the found pages
def final_query(texts, query):
    query_summary = client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": "You are an interactive Space Shuttle manual."},
            {"role": "user", "content": query + ' ' + ' '.join(texts) + " Use the provided manual excerpts to give a detailed response to the query."}
        ]
    )
    message = query_summary.choices[0].message.content
    console_text.config(state="normal")
    console_text.insert(tk.END, f"Final Response: {message}\n")
    console_text.yview(tk.END)
    console_text.config(state="disabled")

def print_to_console(message):
    console_text.config(state="normal")
    console_text.insert(tk.END, message + "\n")
    console_text.yview(tk.END)
    console_text.config(state="disabled")
# Function to handle the search button click event
def on_search_button_click():
    query = query_entry.get()
    if query:
        console_text.delete(1.0, tk.END)
        console_text.config(state="normal")
        console_text.insert(tk.END, f"Processing query: {query}\n\n")
        console_text.yview(tk.END)
        console_text.config(state="disabled")
        
        # Get query embedding and find the closest page
        query_embedding = get_query_embedding(query)
        find_closest_page(query_embedding, manual_path)
        
        # Get page information
        get_page_info(pages)
        
        # Generate the final response
        final_query(texts, query)
    query_entry.delete(0, tk.END)

def on_openpage_button_click():
    if len(pages) != 0:
        console_text.delete(1.0, tk.END)
        console_text.config(state="normal")
        console_text.insert(tk.END, f"\n")
        # Display page information here (for example, file path and page number)
        for page in pages:
            console_text.insert(tk.END, f"Document: {page['filepath']} |  Page : {page['page']}")
        console_text.yview(tk.END)
        console_text.config(state="disabled")
    else:
        console_text.delete(1.0, tk.END)
        console_text.config(state="normal")
        console_text.insert(tk.END, f"No query given\n")
        console_text.yview(tk.END)
        console_text.config(state="disabled")
        
# Bind the search button to the function
search_button.config(command=on_search_button_click)
open_page_button.config(command=on_openpage_button_click)
# Run the application
root.mainloop()
