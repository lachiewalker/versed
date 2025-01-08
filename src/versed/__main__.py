from app import DocumentChat

try:
    app = DocumentChat("versed")
    app.run()
finally:
    app.milvus_client.close()