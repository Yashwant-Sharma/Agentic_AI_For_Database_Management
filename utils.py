READ_ONLY_KEYWORDS = {"select", "show", "describe", "desc", "explain"}


def split_sql_statements(query: str):
    return [part.strip() for part in query.split(";") if part.strip()]


def is_read_only_statement(statement: str) -> bool:
    stripped = statement.strip().lower()
    if not stripped:
        return True
    first_word = stripped.split()[0]
    return first_word in READ_ONLY_KEYWORDS


def requires_confirmation(query: str) -> bool:
    statements = split_sql_statements(query)
    if not statements:
        return False
    return any(not is_read_only_statement(statement) for statement in statements)


def validate_query(query: str):
    # Keep basic validation hook for future extension.
    # We now allow destructive queries, but route them through confirmation.
    return bool(split_sql_statements(query))