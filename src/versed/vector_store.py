import json
from pymilvus import MilvusClient, FieldSchema, DataType, CollectionSchema
from typing import Dict, List

class VectorStore:

    def __init__(self, data_dir, default_collection_name):
        milvus_db_path = data_dir / "milvus.db"
        self.milvus_metadata_path = data_dir / "metadata.json"
        self.milvus_uri = f"{milvus_db_path}"

        self.fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128),
        ]

        self.milvus_client = MilvusClient(uri=self.milvus_uri)

        if not self.milvus_client.list_collections():
            if not self.milvus_client.has_collection(collection_name=default_collection_name):
                schema = CollectionSchema(self.fields, description="Default project for Versed.")
                self.milvus_client.create_collection(collection_name=default_collection_name, schema=schema)

            self.metadata = {
                "collections": [ 
                    { 
                        "collection_name": default_collection_name,
                        "files": []
                    }
                ]
            }
            self.update_metadata()

        else:
            # Load metadata
            with self.milvus_metadata_path.open("r") as file:
                try:
                    self.metadata = json.loads(file.read())
                except json.decoder.JSONDecodeError:
                    # Metadata is corrupted, delete all collections and start fresh
                    self.metadata = { "collections": [] }

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
        if collection_name in self.get_collection_names:
            return self.milvus_client.get_collection_stats(collection_name)
        else:
            return {}

    def add_collection(self, collection_name, description="A searchable file collection.", callback=None) -> bool:
        """
        Adds a collection to the vector store, and its metadata to the metadata file.

        Returns
            bool: A boolean indicating whether the operation succeeded.
        """
        if not self.milvus_client.has_collection(collection_name=collection_name):
            schema = CollectionSchema(self.fields, description=description)
            self.milvus_client.create_collection(collection_name=collection_name, schema=schema)

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

    def remove_collection(self, collection) -> bool:
        """
        Removes a collection from the vector store, and its metadata from the metadata file.

        Returns
            bool: A boolean indicating whether the operation succeeded.
        """
        pass

    def add_to_collection(self, collection ,files) -> bool:
        """
        Adds files to a collection, and updates the collections metadata accordingly.

        Returns
            bool: A boolean indicating whether the operation succeeded.
        """
        pass

    def remove_from_collection(self, collection, files) -> bool:
        """
        Removes files from a collection, and updates the collections metadata accordingly.

        Returns
            bool: A boolean indicating whether the operation succeeded.
        """
        pass