# import psycopg2
# from urfube.config import settings
#
# conn = psycopg2.connect(host=settings.host, user=settings.user, password=settings.password)
# conn.autocommit = True
# conn.cursor().execute(f'CREATE DATABASE {settings.database_name}')
# conn.close()