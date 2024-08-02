import re
from lxml import etree
from bs4 import BeautifulSoup
from scrapy.exceptions import DropItem
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Marker strings for text processing
TRAILING_CATALOG_STRINGS = [
"""Back to Top | Print-Friendly Page (opens a new window)
All catalogs 2024 Oberlin College and Conservatory.
Powered by Modern Campus Catalog.""",

"""All catalogs 2024 Oberlin College and Conservatory.
Powered by Modern Campus Catalog."""
]

TRAILING_OFFICIAL_STRINGS = [
"""College of Arts & Sciences
Conservatory of Music
Admissions & Aid
Life at Oberlin
About Oberlin
News & Events
Campus Resources
Request Info
Visit & Connect
Apply
Give
College of Arts and Sciences Admissions (800) 622-6243 or (440) 775-8411 38 E. College St., Oberlin, OH 44074
Conservatory of Music Admissions (440) 775-8413 39 W. College St., Oberlin, OH 44074
 2024, Oberlin College and Conservatory
Privacy Policy
Copyright Policy
Accreditation
Website Accessibility
Contact Us
Current Students
Alumni
Faculty & Staff
Parents
Local Community
Job Seekers
Apply to Oberlin
Oberlin has separate application processes for the College of Arts and Sciences and the Conservatory of Music.
College of ArtsandSciences Admissions
Conservatory ofMusic Admissions
Double Degree Program
Double Degree Program Applicants
You have exceptional musical talent and intellectual enthusiasm.We have a place just for you."""
]

STRING_BEFORE_COURSE_DESCRIPTION = """New for 2024-25
2024-25 Academic Calendar
My Portfolio"""

STRING_AFTER_COURSE_DESCRIPTION = """[PRELIMINARY] Course Catalog 2024-2025 Add to Portfolio (opens a new window)"""

# Chunk indices for removing unwanted text
FIRST_CATALOG_CHUNK_INDEX = 1
LAST_CATALOG_CHUNK_INDEX = -1       # Relative to the end of the list

FIRST_OFFICIAL_CHUNK_INDEX = 6
LAST_OFFICIAL_CHUNK_INDEX = -1      # Relative to the end of the list

# Chunk size constraints
MIN_CHUNK_SIZE = 128
MAX_CHUNK_SIZE = 512
MAX_CHARACTERS_PER_CHUNK = 3000

# Modified from source code https://github.com/langchain-ai/langchain/blob/master/libs/text-splitters/langchain_text_splitters/html.py
# Transform original HTML using XSLT to add headers and chunks.
def split_html_by_header(html):
    parser = etree.HTMLParser()
    try:
        tree = etree.fromstring(html, parser)
    except:
        raise DropItem("Failed to parse HTML")
    xslt_tree = etree.parse("obot_scraper/text_processing/html_chunks_with_headers.xslt")
    transform = etree.XSLT(xslt_tree)
    result = transform(tree)

    result_dom = etree.fromstring(str(result))
    
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
        ("h4", "Header 4"),
        ("h5", "Header 5"),
        ("h6", "Header 6"),
    ]
    # create filter and mapping for header metadata
    header_filter = [header[0] for header in headers_to_split_on]
    header_mapping = dict(headers_to_split_on)
    # map xhtml namespace prefix
    ns_map = {"h": "http://www.w3.org/1999/xhtml"}

    # build list of elements from DOM
    elements = []
    for element in result_dom.findall("*//*", ns_map):
        if element.findall("*[@class='headers']") or element.findall("*[@class='chunk']"):
            elements.append({
                "content": "".join(
                    [
                        node.text or ""
                        for node in element.findall("*[@class='chunk']", ns_map)
                    ]
                ),
                "metadata": {
                    # Add text of specified headers to metadata using header mapping.
                    header_mapping[node.tag]: node.text or ""
                    for node in filter(
                        lambda x: x.tag in header_filter,
                        element.findall("*[@class='headers']/*", ns_map),
                    )
                },
            })
    
    # aggregate chunks with the same metadata
    aggregated_chunks = []

    for element in elements:
        if (aggregated_chunks and aggregated_chunks[-1]["metadata"] == element["metadata"]):
            # If the last element in the aggregated list has the same metadata as the current element, append the current content to the last element's content
            aggregated_chunks[-1]["content"] += "  \n" + element["content"]
        else:
            # Otherwise, append the current element to the aggregated list
            aggregated_chunks.append(element)

    return aggregated_chunks

# Fix trailing and leading text in the chunks to remove unwanted text
def fix_trailing_leading_texts(chunks):
    # Extract course description from the first chunk (if it exists)
    start_index = chunks[0]["content"].find(STRING_BEFORE_COURSE_DESCRIPTION) + len(STRING_BEFORE_COURSE_DESCRIPTION)
    end_index = chunks[0]["content"].find(STRING_AFTER_COURSE_DESCRIPTION)
    course_description = chunks[0]["content"][start_index:end_index].strip()
    if course_description != "":
        chunks.insert(2, {"metadata": {}, "content": course_description})
    
    # Removing trailing text from the last chunk (if it exists)
    for trailing_catalog_string in TRAILING_CATALOG_STRINGS:
        if chunks[-1]["content"] != trailing_catalog_string and chunks[-1]["content"].endswith(trailing_catalog_string):
            chunks[-1]["content"] = chunks[-1]["content"][:-len(trailing_catalog_string)] 
            chunks.append({"metadata": {}, "content": trailing_catalog_string})
            break
    for trailing_official_string in TRAILING_OFFICIAL_STRINGS:
        if chunks[-1]["content"] != trailing_official_string and chunks[-1]["content"].endswith(trailing_official_string):
            chunks[-1]["content"] = chunks[-1]["content"][:-len(trailing_official_string)] 
            chunks.append({"metadata": {}, "content": trailing_official_string})
            break
    return chunks

def clean_text(text):
    text = text.strip()                         # Remove leading and trailing whitespace
    text = re.sub(r'[^\x00-\x7F]+', '', text)   # Remove non-ASCII characters
    text = re.sub(' +', ' ', text)              # Remove extra spaces
    text = re.sub(' \n', '\n', text)            # Remove extra spaces before newline
    text = re.sub('\n+', '\n', text)            # Remove extra newlines
    
    return text

def split_large_chunk(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = MAX_CHUNK_SIZE,
        chunk_overlap = 0,
        length_function = lambda x: len(x.split()),
        separators = ["\n\n", "\n", ".", " ", ""]
    )
    return splitter.split_text(text)

def preprocess_html(html):
    # Remove the tags that subsite-menu and view-content in their classes (Things like "You may like" and "Related Stories")
    soup = BeautifulSoup(html, 'html.parser')
    tags_to_remove = soup.find_all(class_=lambda x: x and ('subsite-menu' in x.split() or 'view-content' in x.split()))

    for tag in tags_to_remove:
        tag.decompose()

    return str(soup)

def html_to_chunks(html, type="catalog"):
    # Remove unwanted chunks
    if type in ["official", "news", "event", "blog", "bulletin"]:
        first_chunk_index = FIRST_OFFICIAL_CHUNK_INDEX
        last_chunk_index = LAST_OFFICIAL_CHUNK_INDEX
    elif type == "catalog":
        first_chunk_index = FIRST_CATALOG_CHUNK_INDEX
        last_chunk_index = LAST_CATALOG_CHUNK_INDEX
    else:   # External
        first_chunk_index = 0
        last_chunk_index = 0

    html = preprocess_html(html)

    chunks = split_html_by_header(html)

    for i in range(len(chunks)):
        chunks[i]["content"] = clean_text(chunks[i]["content"])

    chunks = fix_trailing_leading_texts(chunks)

    # print("Number of chunks:", len(chunks))
    # for i in range(len(chunks)):
    #     print(chunks[i]["metadata"])
    #     print(chunks[i]["content"])
    #     print("---------------------")
    
    # Extract text chunks, extract headers and title to concatenate with text, split large chunks into smaller chunks
    text_chunks = []
    title = ""
    for i in range(first_chunk_index, len(chunks) + last_chunk_index):
        header_lst = sorted(list(chunks[i]["metadata"].keys()))
        if len(header_lst) > 0 and header_lst[0] == "Header 1" and title == "":
            title = chunks[i]["metadata"]["Header 1"]
        
        header_str = ""
        for header in header_lst[:-1]:
            header_str += chunks[i]["metadata"][header] + " > "

        small_chunks = [chunks[i]["content"]]
        if len(chunks[i]["content"].split()) > MAX_CHUNK_SIZE or len(chunks[i]["content"]) > MAX_CHARACTERS_PER_CHUNK:
            small_chunks = split_large_chunk(chunks[i]['content'])
        
        # Each small chunk is concatenated with the header string
        for small_chunk in small_chunks:
            text_chunks.append(header_str + small_chunk)
    
    # Aggregate small chunks into larger chunks 
    aggregated_text_chunks = []
    cur_chunk = ""
    for text_chunk in text_chunks:
        if len(cur_chunk.split())  < MIN_CHUNK_SIZE:
            cur_chunk += text_chunk + "\n------\n"
        else:
            aggregated_text_chunks.append(cur_chunk)
            cur_chunk = text_chunk + "\n------\n"
    if cur_chunk != "":
        if len(cur_chunk.split()) < MIN_CHUNK_SIZE and len(aggregated_text_chunks) > 0:
            aggregated_text_chunks[-1] += cur_chunk
        else:
            aggregated_text_chunks.append(cur_chunk)

    # Add title to the beginning of each chunk
    aggregated_text_chunks = [chunk if chunk.startswith(title) else title.upper() + "\n" + chunk for chunk in aggregated_text_chunks]

    # print("Number of text chunks:", len(aggregated_text_chunks))
    # for i in range(len(aggregated_text_chunks)):
    #     print(aggregated_text_chunks[i])
    #     print("===============")

    return aggregated_text_chunks
    
