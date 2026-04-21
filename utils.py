def validate_query(query):
    forbidden = ["DROP", "TRUNCATE"]

    for word in forbidden:
        if word in query.upper():
            return False

    return True