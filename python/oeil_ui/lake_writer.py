from azure.storage.blob import ContainerClient


class LakeWriter:

    def __init__(self, sas_url: str):
        if not sas_url:
            raise ValueError("Missing OEIL_AZCOPY_DEST (SAS URL)")

        self.container_client = ContainerClient.from_container_url(sas_url)

    def write_policy(self, path: str, content: str):

        self.container_client.upload_blob(
            name=path,
            data=content,
            overwrite=True
        )

    def policy_exists(self, path: str) -> bool:

        blob_client = self.container_client.get_blob_client(path)
        return blob_client.exists()