from __future__ import annotations

import shutil
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.client import Config

from app.core.config import settings


class StorageService:
    def put_file(self, source_path: Path, key: str, content_type: str | None = None) -> str:
        raise NotImplementedError

    def download_file(self, key: str, destination_path: Path) -> Path:
        raise NotImplementedError

    def url_for(self, key: str) -> str | None:
        raise NotImplementedError

    def local_path_for(self, key: str) -> Path | None:
        return None


class LocalStorageService(StorageService):
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root.resolve() not in path.parents and path != self.root.resolve():
            raise ValueError("Invalid storage key")
        return path

    def put_file(self, source_path: Path, key: str, content_type: str | None = None) -> str:
        destination = self._resolve(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination)
        return key

    def download_file(self, key: str, destination_path: Path) -> Path:
        source = self._resolve(key)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination_path)
        return destination_path

    def url_for(self, key: str) -> str | None:
        return None

    def local_path_for(self, key: str) -> Path | None:
        return self._resolve(key)


class S3StorageService(StorageService):
    def __init__(self) -> None:
        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET is required for s3 storage")
        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            region_name=settings.s3_region,
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            config=Config(signature_version="s3v4"),
        )

    def put_file(self, source_path: Path, key: str, content_type: str | None = None) -> str:
        extra_args = {"ContentType": content_type} if content_type else None
        self.client.upload_file(str(source_path), self.bucket, key, ExtraArgs=extra_args or {})
        return key

    def download_file(self, key: str, destination_path: Path) -> Path:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(self.bucket, key, str(destination_path))
        return destination_path

    def url_for(self, key: str) -> str | None:
        if settings.s3_public_base_url:
            return f"{settings.s3_public_base_url.rstrip('/')}/{key}"
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=settings.presigned_url_ttl_seconds,
        )


@lru_cache
def get_storage() -> StorageService:
    if settings.storage_backend == "s3":
        return S3StorageService()
    return LocalStorageService(settings.local_storage_path)

