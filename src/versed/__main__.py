from versed.app import DocumentChat

def cli():
    try:
        app = DocumentChat("versed")
        app.run()
    finally:
        app.vector_store.close_client()