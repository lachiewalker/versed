from versed.app import DocumentChat

def cli():
    try:
        app = DocumentChat("versed")
        app.run()
    finally:
        app.milvus_client.close()