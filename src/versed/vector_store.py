import json
from typing import Dict, List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pymilvus import MilvusClient, FieldSchema, DataType, CollectionSchema
from versed.file_handler import FileHandler

class VectorStore:

    def __init__(
        self,
        app,
        data_dir,
        default_collection_name,
        google_credentials
    ):
        self.app = app

        milvus_db_path = data_dir / "milvus.db"
        self.milvus_metadata_path = data_dir / "metadata.json"
        self.milvus_uri = f"{milvus_db_path}"

        self.fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),
        ]

        self.milvus_client = MilvusClient(uri=self.milvus_uri)
        self.metadata = { "collections": [] }

        if not self.milvus_client.list_collections():
            if not self.milvus_client.has_collection(collection_name=default_collection_name):
                self.add_collection(collection_name=default_collection_name, description="Default project for Versed.")
        else:
            # Load metadata
            with self.milvus_metadata_path.open("r") as file:
                try:
                    self.metadata = json.loads(file.read())
                except json.decoder.JSONDecodeError:
                    # Metadata is corrupted, delete all collections and start fresh?
                    self.metadata = { "collections": [] }

        self.openai_client = None
        self.google_credentials = google_credentials

        self.file_handler = FileHandler(self.google_credentials)

    def initialise_openai_client(self, api_key) -> OpenAI | None:
        self.openai_client = OpenAI(api_key=self.app.api_key)

    def close_client(self) -> None:
        self.milvus_client.close()

    def update_metadata(self) -> bool:
        """
        Updates the metadata file.

        Returns
            bool: A boolean indicating whether the operation succeeded.
        """
        with self.milvus_metadata_path.open("w") as file:
            file.write(json.dumps(self.metadata) + "\n")
        return True

    def get_collection_names(self) -> List:
        return [x["collection_name"] for x in self.metadata["collections"]]
    
    def get_collection_stats(self, collection_name) -> Dict:
        if collection_name in self.get_collection_names():
            return self.milvus_client.get_collection_stats(collection_name)
        else:
            return {}

    def add_collection(self, collection_name: str, description: str="A searchable file collection.", callback=None) -> bool:
        """
        Adds a collection to the vector store, and its metadata to the metadata file.

        Returns
            bool: A boolean indicating whether the operation succeeded.
        """
        if not collection_name in self.milvus_client.list_collections():
            schema = CollectionSchema(self.fields, description=description, auto_id=True)
            self.milvus_client.create_collection(collection_name=collection_name, schema=schema)

            # Add indexes
            index_params = self.milvus_client.prepare_index_params()
            index_params.add_index(
                field_name="embedding", 
                index_type="AUTOINDEX",
                metric_type="COSINE"
            )

            # Update vector store metadata
            collection_metadata = { 
                "collection_name": collection_name,
                "files": []
            }
            self.metadata["collections"].append(collection_metadata)
            self.update_metadata()

            if callback:
                callback()
            return True
        else:
            return False

    def remove_collection(self, collection_name: str, callback=None) -> bool:
        """
        Removes a collection from the vector store, and its metadata from the metadata file.

        Returns
            bool: A boolean indicating whether the operation succeeded.
        """
        if collection_name in self.milvus_client.list_collections():
            response = self.milvus_client.drop_collection(collection_name=collection_name)

            # Update vector store metadata
            self.metadata["collections"] = [
                c for c in self.metadata["collections"] 
                if c["collection_name"] != collection_name
            ]
            self.update_metadata()

            if callback:
                callback()
            return True
        else:
            return False

    def add_files_to_collection(self, collection, files) -> bool:
        """
        Adds files to a collection, and updates the collections metadata accordingly.

        Returns
            bool: A boolean indicating whether the operation succeeded.
        """
        for file in files:
            content = self.get_file_content(file)
            chunks = self.split_text(content)
            vectors = self.embed_chunks(chunks)
            # Handle metadata here
            self.add_to_collection(collection, vectors)

    def remove_files_from_collection(self, collection: str, files: List[Dict]) -> bool:
        """
        Removes files from a collection, and updates the collections metadata accordingly.

        Returns
            bool: A boolean indicating whether the operation succeeded.
        """
        pass

    def get_file_content(self, file) -> str:
        return self.file_handler.get_file_content(file)

    async def chunk_file(self, file_contents: str) -> List[str]:
        """
        """
        long_context = f"""
        <document>
        {file_contents}
        </document>
        """

        chunking_instructions = ""

        response = await self.openai_client.chat.completions.create(
            messages=[
                {"role": "system", "content": long_context},
                {"role": "user", "content": chunking_instructions},
            ],
            model="gpt-4o-mini",
        )
        return response.choices[0].message.content
    
    def split_text(self, text, chunk_size=500, overlap=0) -> List[str]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
            is_separator_regex=False,
            separators=[
                ".\n\n",
                "\n\n",
                ".\n",
                "\n",
                ".",
                ",",
                " ",
                "\u200b",  # Zero-width space
                "\uff0c",  # Fullwidth comma
                "\u3001",  # Ideographic comma
                "\uff0e",  # Fullwidth full stop
                "\u3002",  # Ideographic full stop
                "",
            ],
        )

        return text_splitter.split_text(text)

    def embed_chunks(self, chunks):
        """
        Embeds a list of chunks and returns a dictionary associating each
        text with its embedding.

        Returns:
            Dict: {
                "text": str: The chunk text,
                "embedding": List[float]: The chunk embedding.
            }
        """
        response = self.openai_client.embeddings.create(
            input=chunks,
            model="text-embedding-3-small",
            dimensions=1024
        )

        chunk_documents = []
        for i, chunk_response in enumerate(response.data):
            embedding = chunk_response.embedding
            chunk_document = { 
                "text": chunks[i],
                "embedding": embedding 
            }
            chunk_documents.append(chunk_document)

        return chunk_documents

    def add_to_collection(self, collection, data):
        # Insert into Milvus collection
        response = self.milvus_client.insert(collection_name=collection, data=data)
        response_dict = dict(response)
        # Check all entities added ?
        # if response_dict["insert_count"] != len(data):
        #     pass
        # self.app.push_screen(DebugScreen(json_response))

        # try:
        #     response = self.milvus_client.insert(collection_name=collection, data=data)
        # except Exception as e:
        #     self.app.push_screen(DebugScreen(e))
        
        return
