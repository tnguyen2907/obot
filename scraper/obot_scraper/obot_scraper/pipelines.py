# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
from itemadapter import ItemAdapter
from datetime import datetime, timezone, timedelta
import hashlib
import logging
from io import BytesIO
from obot_scraper.processing_utils.html import html_to_chunks
from obot_scraper.processing_utils.file import file_to_chunks

from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_query import FieldFilter
from vertexai.preview.language_models import TextEmbeddingModel, TextEmbeddingInput

EDT_timezone = timezone(timedelta(hours=-4), 'EDT')

# STANDARD_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %z"
OFFICIAL_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
# CATALOG_TIME_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"

EVENT_DATE_HAPPENED_TIME_FORMAT = "%Y-%m-%d"
NEWS_DATE_HAPPENED_TIME_FORMAT = "%B %d, %Y"
BULLETIN_DATE_HAPPENED_TIME_FORMAT = "%B %d, %Y %I:%M %p"
BLOG_DATE_HAPPENED_TIME_FORMAT = "%B %d, %Y"

GCP_PROJECT_ID = os.environ["GCP_PROJECT_ID"]

class CleaningAndChunkingPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Convert time to datetime object
        if adapter['website_last_modified_time'] != None:
            adapter['website_last_modified_time'] = datetime.strptime(adapter['website_last_modified_time'], OFFICIAL_TIME_FORMAT)
        adapter['scraped_time'] = datetime.now(EDT_timezone)
        
        # Convert date_happened to datetime object (only for event, news, bulletin, blog)
        if adapter['metadata']['date_happened'] != None:
            try:
                if adapter['type'] == 'event':
                    adapter['metadata']['date_happened'] = datetime.strptime(adapter['metadata']['date_happened'], EVENT_DATE_HAPPENED_TIME_FORMAT).replace(tzinfo=EDT_timezone)
                elif adapter['type'] == 'news':
                    adapter['metadata']['date_happened'] = datetime.strptime(adapter['metadata']['date_happened'], NEWS_DATE_HAPPENED_TIME_FORMAT).replace(tzinfo=EDT_timezone)
                elif adapter['type'] == 'bulletin':
                    adapter['metadata']['date_happened'] = datetime.strptime(adapter['metadata']['date_happened'], BULLETIN_DATE_HAPPENED_TIME_FORMAT).replace(tzinfo=EDT_timezone)
                elif adapter['type'] == 'blog':
                    adapter['metadata']['date_happened'] = datetime.strptime(adapter['metadata']['date_happened'], BLOG_DATE_HAPPENED_TIME_FORMAT).replace(tzinfo=EDT_timezone)
            except Exception as e:
                logging.warning("Failed to convert date_happened to datetime object for url: {}. Exception: {}".format(adapter['url'], e))  
                adapter['metadata']['date_happened'] = None
                
        # Convert content to chunks
        if adapter['url'].endswith(('.pdf', '.docx', '.pptx', '.xlsx')) or adapter['url'].startswith(("https://drive.google.com", "https://drive.usercontent.google.com")):
            chunks = file_to_chunks(file=BytesIO(adapter['content']), url=adapter['url'])
        else:
            chunks = html_to_chunks(html=adapter['content'], type=adapter['type'])

        adapter['content'] = chunks

        # Calculate hash value
        def hash_text(text):
            return hashlib.md5(text.encode()).hexdigest()
        full_text = "\n".join(chunks)
        adapter['hash_value'] = hash_text(full_text)

        return item



class EncodingAndStoringPipeline:
    # URL and encoding stats
    num_new_urls = 0
    new_url_lst = []
    num_updated_urls = 0
    updated_url_lst = []
    num_new_encoded_docs = 0
    total_tokens = 0
    total_billable_characters = 0

    def __init__(self):
        self.db = firestore.Client(project=GCP_PROJECT_ID, database="(default)")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if adapter['content'] == []:
            return item
        
        docs = self.db.collection('metadata').where(filter=FieldFilter('url', '==', adapter['url'])).get()

        def add_embedding_to_db():
            # print("Adding embeddings to db")
            chunks = adapter['content']
            
            embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            count_token_response = embedding_model.count_tokens(chunks)

            text_embedding_inputs = [TextEmbeddingInput(task_type="RETRIEVAL_DOCUMENT", text=chunks[i]) for i in range(len(chunks))]
            try:
                embeddings = embedding_model.get_embeddings(text_embedding_inputs)
            except Exception as e:
                logging.warning("Failed to get embeddings in one go. Splitting the text into smaller chunks and trying again. Exception: {}".format(e))
                embeddings = [embedding_model.get_embeddings([text_embedding_input])[0] for text_embedding_input in text_embedding_inputs]

            logging.debug("Total tokens: {}. Total billable characters: {}".format(count_token_response.total_tokens, count_token_response.total_billable_characters))

            EncodingAndStoringPipeline.total_tokens += count_token_response.total_tokens
            EncodingAndStoringPipeline.total_billable_characters += count_token_response.total_billable_characters
            
            for i in range(len(embeddings)):
                self.db.collection('vector_index').add({
                    'url': adapter['url'],
                    'type': adapter['type'],
                    'content': chunks[i],      
                    'embedding': Vector(embeddings[i].values),
                    'metadata': adapter['metadata']
                })
                EncodingAndStoringPipeline.num_new_encoded_docs += 1

        
        def delete_embedding_from_db(): 
            # print("Deleting embeddings from db")
            docs = self.db.collection('vector_index').where(filter=FieldFilter('url', '==', adapter['url'])).stream()
            for doc in docs:
                doc.reference.delete()

        def is_modified():
            check_by_time = ['official', 'news', 'event', 'blog', 'bulletin']
            check_by_hash = ['catalog', 'external', 'file']
            if adapter['type'] in check_by_time:
                if adapter['website_last_modified_time'] > docs[0].to_dict()['website_last_modified_time']:
                    return True
            elif adapter['type'] in check_by_hash:
                if adapter['hash_value'] != docs[0].to_dict()['hash_value']:
                    return True
            return False
        
        if len(docs) == 0:  # If the document does not exist in the database, create a new document
            logging.debug("Creating a new document and adding embeddings")
            
            self.db.collection('metadata').add({
                'url': adapter['url'],
                'type': adapter['type'],
                'website_last_modified_time': adapter['website_last_modified_time'],
                'scraped_time': adapter['scraped_time'],
                'hash_value': adapter['hash_value'],
            })
            add_embedding_to_db()

            EncodingAndStoringPipeline.num_new_urls += 1  
            EncodingAndStoringPipeline.new_url_lst.append(adapter['url'])

        else:   # If the document exists in the database, update the existing document
            if is_modified():   # doc modified, update the document scrape time and replace the embeddings
                logging.debug("Updating existing document and replacing embeddings")
                self.db.collection('metadata').document(docs[0].id).update({
                    'type': adapter['type'],
                    'website_last_modified_time': adapter['website_last_modified_time'],
                    'scraped_time': adapter['scraped_time'],
                    'hash_value': adapter['hash_value'],
                })
                delete_embedding_from_db()  # Delete old embeddings
                add_embedding_to_db()       # Add new embeddings

                EncodingAndStoringPipeline.num_updated_urls += 1
                EncodingAndStoringPipeline.updated_url_lst.append(adapter['url'])
            else:   # doc not modified, only update the document scrape time
                logging.debug("Updating existing document")
                self.db.collection('metadata').document(docs[0].id).update({
                    'type': adapter['type'],
                    'website_last_modified_time': adapter['website_last_modified_time'],
                    'scraped_time': adapter['scraped_time'],
                    'hash_value': adapter['hash_value'],
                })


        return item
    
    @classmethod
    def print_stats(cls):
        logging.info("Number of new websites: " + str(cls.num_new_urls))
        logging.info("New URLs: " + str(cls.new_url_lst))
        logging.info("Number of updated websites: " + str(cls.num_updated_urls))
        logging.info("Updated URLs: " + str(cls.updated_url_lst))
        logging.info("Number of new encoded documents: " + str(cls.num_new_encoded_docs))
        logging.info("Total tokens: " + str(cls.total_tokens))
        logging.info("Total billable characters: " + str(cls.total_billable_characters))

    
