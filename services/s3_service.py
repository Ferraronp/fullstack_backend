import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.getenv("S3_BUCKET", "finance-files")
PRESIGNED_URL_EXPIRES = 3600  # 1 час

ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/webp",
    "application/pdf",
    "text/plain",
}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def _get_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )


def ensure_bucket():
    client = _get_client()
    try:
        client.head_bucket(Bucket=S3_BUCKET)
    except ClientError:
        client.create_bucket(Bucket=S3_BUCKET)


def upload_file(file_bytes: bytes, original_filename: str, content_type: str) -> str:
    """Загружает файл в S3 и возвращает s3_key."""
    ext = original_filename.rsplit(".", 1)[-1] if "." in original_filename else ""
    s3_key = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())

    client = _get_client()
    client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return s3_key


def get_presigned_url(s3_key: str) -> str:
    """Возвращает временную ссылку на скачивание файла."""
    client = _get_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": s3_key},
        ExpiresIn=PRESIGNED_URL_EXPIRES,
    )


def delete_file(s3_key: str) -> None:
    client = _get_client()
    client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
