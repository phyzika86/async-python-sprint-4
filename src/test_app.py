from fastapi.testclient import TestClient
from utils import session_utils
import psycopg2
from psycopg2.extras import NamedTupleCursor

from main import app

client = TestClient(app)
get_session = session_utils.get_session


def test_read_root():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == "Добро пожаловать в сервис по созданию сокращенной формы передаваемых url"


def test_create_url():
    response = client.post('/url', json={'target_url': 'https://realpython.com/'})
    assert response.status_code == 200
    data = response.json()
    assert data['target_url'] == 'https://realpython.com/'


def test_forward_to_target_url():
    pass


def test_butch_upload_file():
    # conString = "postgres://YourUserName:YourPassword@YourHostname:5432/YourDatabaseName";
    conn = psycopg2.connect(dbname='collection', user='postgres', password='postgres', host='localhost')
    cursor = conn.cursor()
    cursor.execute('delete from urls')
    cursor.execute('commit')
    with open('butch_upload_urls.txt', 'rb') as f:
        files = {'file': ('test_file.docx', f)}
        response = client.post('/file/upload-file', json={}, files=files)
    assert response.status_code == 200
    cursor.execute('select target_url from urls')
    all_urls = cursor.fetchall()
    assert len(all_urls) == 3
    cursor.close()
    conn.close()


def test_forward_to_target_url_with_error():
    response = client.get('/ABCD12345')
    assert response.status_code == 404


def test_forward_to_target_url_success():
    conn = psycopg2.connect(dbname='collection', user='postgres', password='postgres', host='localhost')
    cursor = conn.cursor(cursor_factory=NamedTupleCursor)
    cursor.execute('delete from urls')
    cursor.execute('commit')
    with open('butch_upload_urls.txt', 'rb') as f:
        files = {'file': ('test_file.docx', f)}
        response = client.post('/file/upload-file', json={}, files=files)
    cursor.execute('select * from urls')
    all_urls = cursor.fetchall()

    first_url = all_urls[0]
    url = f'/{first_url.key}'
    response = client.get('url')
    assert response.status_code == 200
