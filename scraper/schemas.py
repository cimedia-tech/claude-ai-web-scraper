from pydantic import BaseModel, field_validator
from typing import Optional


class LeadData(BaseModel):
    """Primary extraction schema for lead generation scraping."""
    company: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v and "@" not in v:
            return None
        return v


class ProductData(BaseModel):
    """Extraction schema for e-commerce / product scraping."""
    name: str
    price: Optional[str] = None
    currency: Optional[str] = None
    availability: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[str] = None
    reviews_count: Optional[int] = None


class ArticleData(BaseModel):
    """Extraction schema for news / blog / content scraping."""
    title: str
    author: Optional[str] = None
    published_date: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[list[str]] = None
    url: Optional[str] = None
    word_count: Optional[int] = None


class GenericData(BaseModel):
    """Flexible schema for ad-hoc extraction tasks."""
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[dict] = None
    url: Optional[str] = None


SCHEMA_MAP = {
    "lead": LeadData,
    "product": ProductData,
    "article": ArticleData,
    "generic": GenericData,
}
