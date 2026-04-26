import database
print(f'Database module location: {database.__file__}')
print(f'Has list_projects: {hasattr(database, "list_projects")}')
print(f'Has get_projects: {hasattr(database, "get_projects")}')
