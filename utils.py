# utils.py
def validate_query(query):
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "GRANT", "REVOKE", "TRUNCATE"]
    for word in forbidden:
        if word in query.upper():
            return False
    return True