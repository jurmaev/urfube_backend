from fastapi.testclient import TestClient
from urfube.app import app, get_db
from peewee import *
from urfube.database import PeeweeConnectionState
from urfube import models
from urfube.utils import *

test_db = peewee.SqliteDatabase('urfube/tests/test.db', check_same_thread=False)
test_db._state = PeeweeConnectionState()
test_db.connect()
test_db.drop_tables([models.User, models.Video, models.History])
test_db.create_tables([models.User, models.Video, models.History])
test_db.close()


def override_get_db():
    try:
        test_db.connect()
        yield
    finally:
        if not test_db.is_closed():
            test_db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def get_json_rpc_body(method, params):
    return {
        'jsonrpc': '2.0',
        'id': 0,
        'method': method,
        'params': params
    }


def test_create_user():
    response = client.post('/api', json={
        'jsonrpc': '2.0',
        'id': 0,
        'method': 'signup',
        'params': {
            'user': {
                'username': 'JohnDoe',
                'password': 'sfamjisoer345',
                'email': 'example@gmail.com'
            }
        }
    })
    assert response.status_code == 200
    data = response.json()['result']
    assert data == 'JohnDoe'


def test_create_same_user():
    response = client.post('/api', json=get_json_rpc_body('signup', {
        'user': {
            'username': 'JohnDoe',
            'password': 'sfamjisoer345',
            'email': 'example@gmail.com'
        }
    }))
    assert response.status_code == 200
    data = response.json()['error']
    assert data['code'] == 1000
    assert data['message'] == 'User already exists'


def test_login_without_scopes():
    response = client.post('/api', json=get_json_rpc_body('login', {
        'user': {
            'username': 'JohnDoe',
            'password': 'sfamjisoer345'
        }
    }))
    assert response.status_code == 200
    data = response.json()['result']
    assert data['access_token'] == create_access_token({'sub': 'JohnDoe', 'scopes': None})
    assert data['refresh_token'] == create_refresh_token({'sub': 'JohnDoe', 'scopes': None})
    assert data['token_type'] == 'bearer'


def test_login_with_scopes():
    response = client.post('/api', json=get_json_rpc_body('login', {
        'user': {
            'username': 'JohnDoe',
            'password': 'sfamjisoer345'
        },
        'scopes': [
            'admin'
        ]
    }
                                                          ))
    assert response.status_code == 200
    data = response.json()['result']
    assert data['access_token'] == create_access_token({'sub': 'JohnDoe', 'scopes': ['admin']})
    assert data['refresh_token'] == create_refresh_token({'sub': 'JohnDoe', 'scopes': ['admin']})
    assert data['token_type'] == 'bearer'


def test_login_wrong_username():
    response = client.post('/api', json=get_json_rpc_body('login', {
        'user': {
            'username': 'JohnDove',
            'password': 'sfamjisoer345'
        }
    }))
    assert response.status_code == 200
    data = response.json()['error']
    assert data['code'] == 1001
    assert data['message'] == 'Wrong username or password'


def test_login_wrong_password():
    response = client.post('/api', json=get_json_rpc_body('login', {
        'user': {
            'username': 'JohnDoe',
            'password': 'wrong_password'
        }
    }))
    assert response.status_code == 200
    data = response.json()['error']
    assert data['code'] == 1001
    assert data['message'] == 'Wrong username or password'


def test_refresh_tokens():
    response = client.post('/api', json=get_json_rpc_body('login', {
        'user': {
            'username': 'JohnDoe',
            'password': 'sfamjisoer345'
        }
    }))
    refresh_token = response.json()['result']['refresh_token']
    response = client.post('/api', json=get_json_rpc_body('refresh_tokens', {
        "refresh_token": refresh_token
    }))
    data = response.json()['result']
    assert response.status_code == 200
    assert data['access_token'] == create_access_token({'sub': 'JohnDoe', 'scopes': None})
    assert data['refresh_token'] == create_refresh_token({'sub': 'JohnDoe', 'scopes': None})
    assert data['token_type'] == 'bearer'


def test_upload_video():
    response = client.post('/api', json=get_json_rpc_body('upload_video', {
        'video': {
            'title': 'test_video',
            'description': 'Cool description'
        }
    }), headers={'User-Auth-Token': create_access_token({'sub': 'JohnDoe', 'scopes': ['admin']})})
    assert response.status_code == 200
    data = response.json()['result']
    assert data['title'] == 'test_video'
    assert data['description'] == 'Cool description'
    assert data['author'] == 'JohnDoe'
    assert data['id'] == 1
    assert data['user_id'] == 1


def test_upload_same_video():
    response = client.post('/api', json=get_json_rpc_body('upload_video', {
        'video': {
            'title': 'test_video',
            'description': 'Cool description'
        }
    }), headers={'User-Auth-Token': create_access_token({'sub': 'JohnDoe', 'scopes': ['admin']})})
    assert response.status_code == 200
    # print(response.json())
    data = response.json()['error']
    assert data['code'] == 2000
    assert data['message'] == 'Video already exists'


def test_get_videos():
    response = client.post('/api', json=get_json_rpc_body('get_videos', {}))

    assert response.status_code == 200
    data = response.json()['result']
    assert data == [{'title': 'test_video',
                     'description': 'Cool description',
                     'author': 'JohnDoe',
                     'link': 'link',
                     'id': 1,
                     'user_id': 1}]


def test_add_history():
    response = client.post(url='/api', json=get_json_rpc_body('add_or_update_history', {
        'video': {
            'video_id': 1,
            'timestamp': 14,
            'date_visited': '2023-03-29T14:58:14.559Z'
        }, 'video_id': 1
    }), headers={'User-Auth-Token': create_access_token({'sub': 'JohnDoe', 'scopes': ['admin']})})
    assert response.status_code == 200


def test_get_user_history():
    response = client.post('/api', json=get_json_rpc_body('get_user_history', {})
                           , headers={'User-Auth-Token': create_access_token({'sub': 'JohnDoe', 'scopes': ['admin']})})
    assert response.status_code == 200
    data = response.json()['result']
    assert data == [
        {
            'video_id': 1,
            'timestamp': 14,
            'date_visited': '2023-03-29T14:58:14.559000+00:00'
        }
    ]


def test_update_user_history():
    client.post('/api', json=get_json_rpc_body('add_or_update_history', {
        'video': {
            'video_id': 1,
            'timestamp': 20,
            'date_visited': '2023-03-29T14:58:14.559Z'
        }, 'video_id': 1
    }), headers={'User-Auth-Token': create_access_token({'sub': 'JohnDoe', 'scopes': ['admin']})})
    response = client.post('/api', json=get_json_rpc_body('get_user_history', {})
                           , headers={'User-Auth-Token': create_access_token({'sub': 'JohnDoe', 'scopes': ['admin']})})
    assert response.status_code == 200
    data = response.json()['result']
    assert data == [{
        'video_id': 1,
        'timestamp': 20,
        'date_visited': '2023-03-29T14:58:14.559000+00:00'
    }]
