from extractor import naive_extract


test_inputs = [
    """
    Ali Khan is applying for a Python Developer position.
    He has 2 years of experience.
    His email is ali@example.com.
    His skills include Python, FastAPI, and PostgreSQL.
    """,

    """
    Sara Ahmed is a Frontend Developer at Tech Solutions.
    She has 3 years of experience.
    Her skills are React, JavaScript, HTML, and CSS.
    """,

    """
    Hamza is looking for a Backend Developer role.
    He has 4 years of experience working with Node.js,
    Express.js and MongoDB.
    """,

    """
    Company: ABC Software
    Position: Full Stack Developer
    Required skills: React, Node.js, MongoDB, Python.
    Experience required: 2 years.
    """,

    """
    We are hiring a Junior Python Developer.
    Candidates should know Python, Django and PostgreSQL.
    Fresh graduates can apply.
    """,

    """
    Maria has applied for the Data Analyst position.
    She knows Python, SQL, Excel and Power BI.
    She has 1 year of experience.
    """,

    """
    XYZ Technologies is hiring a DevOps Engineer.
    Required skills include Docker, Kubernetes, Linux and AWS.
    Minimum experience is 3 years.
    """,

    """
    Ahmed is applying for a Machine Learning Engineer position.
    He has 2 years of experience with Python,
    TensorFlow and machine learning.
    """,

    """
    We need a Software Engineer with experience in C++,
    data structures, algorithms and object-oriented programming.
    """,

    """
    Fatima is applying for an AI Engineer position.
    Her skills include Python, LangChain, APIs and LLMs.
    She has 2 years of professional experience.
    """
]


successful = 0
failed = 0


for i, text in enumerate(test_inputs, start=1):

    try:
        result = naive_extract(text)

        print(f"Test {i}: SUCCESS")
        print(result)
        print()

        successful += 1

    except Exception as error:

        print(f"Test {i}: FAILED")
        print(error)
        print()

        failed += 1


total = len(test_inputs)
failure_rate = (failed / total) * 100


print("=" * 40)
print(f"Total tests: {total}")
print(f"Successful: {successful}")
print(f"Failed: {failed}")
print(f"Failure rate: {failure_rate:.1f}%")
print("=" * 40)