from extractor import naive_extract


text = """
Ali Khan is applying for a Python Developer position.
He has 2 years of experience.
His email is ali@example.com.
His skills include Python, FastAPI, and PostgreSQL.
"""

result = naive_extract(text)

print(result)