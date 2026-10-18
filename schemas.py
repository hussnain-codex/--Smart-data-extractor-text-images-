from datetime import date

from pydantic import BaseModel, Field, model_validator


class LineItem(BaseModel):
    name: str = Field(description="Name of the item")
    quantity: int = Field(gt=0, description="Quantity of the item")
    price: float = Field(ge=0, description="Price of one unit of the item")


class Invoice(BaseModel):
    vendor: str = Field(description="Name of the vendor or store")
    invoice_date: date = Field(description="Date of the invoice")
    items: list[LineItem] = Field(description="List of items in the invoice")
    total: float = Field(ge=0, description="Total amount of the invoice")
    currency: str = Field(description="Currency used in the invoice")

    @model_validator(mode="after")
    def validate_business_rules(self):
        if self.invoice_date > date.today():
            raise ValueError("Invoice date cannot be in the future.")

        calculated_total = sum(
            item.quantity * item.price for item in self.items
        )
        if abs(calculated_total - self.total) > 0.02:
            raise ValueError(
                "Invoice total mismatch. "
                f"Expected {calculated_total:.2f}, "
                f"but invoice says {self.total:.2f}."
            )

        return self


class JobPost(BaseModel):
    title: str = Field(description="Title of the job")
    company: str = Field(description="Name of the company offering the job")
    skills: list[str] = Field(description="Skills required for the job")
    salary_range: str | None = Field(
        default=None,
        description="Salary range mentioned in the job post"
    )