from azure.storage.blob import BlobServiceClient


class LakeWriter:

    def __init__(self, connection_string):
        self.client = BlobServiceClient.from_connection_string(connection_string)

    def write_policy(self, container, path, content):

        blob_client = self.client.get_blob_client(
            container=container,
            blob=path
        )

        blob_client.upload_blob(content, overwrite=True)