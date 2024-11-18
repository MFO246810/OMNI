import os
import pymupdf
import string
from dotenv import load_dotenv
from openai import OpenAI
import json

Api_key = os.getenv('Open_AI_API_Key')
client = OpenAI(api_key=Api_key)
special_characters = set(string.punctuation)
chunks = []
embedded_chunks = []
def chunker(pdf_path):
    counter = 0
    doc = pymupdf.open(pdf_path)
    metadata = doc.metadata
    title = metadata.get("title", "untitled")
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        text = text.replace("\n", " ")
        chunks.append({'Data': text,'Title': title, 'page': page_num, 'filepath' : pdf_path})
    

def embed(text):
    return client.embeddings.create(
    model="text-embedding-3-large",
    input=text,
    encoding_format="float")
    
def save_da_chunk(chunk):
    embedded = embed(chunk['Data'])
    embedded = embedded.data[0].embedding
    embedded_chunk = {'Data': embedded, 'page': chunk['page'], 'filepath': chunk['filepath']}
    embedded_chunks.append(embedded_chunk)   
    print(chunk['page'])

def main(pdf_path, json_path):
    chunker(pdf_path)
    for chunk in chunks:
        save_da_chunk(chunk)
    with open(json_path, 'w') as file:
        json.dump(embedded_chunks, file, indent=4)
    
directory_path = 'SpaceShuttleDocumentation'
Manuals = []
for file_name in os.listdir(directory_path):
    file_path = os.path.join(directory_path, file_name)
    
    if os.path.isfile(file_path):
        j_path = file_path[25 + 1:].strip()
        j_path = j_path[:-4].strip() + ".json"
        Manuals.append(j_path)
        #main(file_path, j_path)
        embedded_chunks = []
with open('selected_manual.json', 'w') as file:
    json.dump(Manuals, file, indent=4)

    