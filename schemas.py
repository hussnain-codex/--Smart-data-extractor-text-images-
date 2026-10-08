from datetime import date
from pydantic import BaseModel, Field


class LineItem(BaseModel):
    name: str = Field(description="Name of the item")
    quantity: int = Field(description="Quantity of the item")
    price: float = Field(description="Price of one unit of the item")


class Invoice(BaseModel):
    vendor: str = Field(description="Name of the vendor or store")
    invoice_date: date = Field(description="Date of the invoice")
    items: list[LineItem] = Field(description="List of items in the invoice")
    total: float = Field(description="Total amount of the invoice")
    currency: str = Field(description="Currency used in the invoice")


class JobPost(BaseModel):
    title: str = Field(description="Title of the job")
    company: str = Field(description="Name of the company offering the job")
    skills: list[str] = Field(description="Skills required for the job")
    salary_range: str | None = Field(
        default=None,
        description="Salary range mentioned in the job post"
    )