from fastapi.testclient import TestClient
from urfube.app import app, get_db
from peewee import *
from urfube.database import PeeweeConnectionState
from urfube import models
from urfube.utils import *
from urfube.crud import *

test_db = peewee.SqliteDatabase('test.db', check_same_thread=False)
test_db._state = PeeweeConnectionState()
test_db.connect()
test_db.bind([models.User, models.Video, models.History])
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
    assert response.json()['result'] is None
    user = get_user_by_username('JohnDoe')
    test_db.close()
    assert user.username == 'JohnDoe'
    assert verify_password('sfamjisoer345', user.password) is True


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
        'refresh_token': refresh_token
    }))
    data = response.json()['result']
    assert response.status_code == 200
    assert data['access_token'] == create_access_token({'sub': 'JohnDoe', 'scopes': None})
    assert data['refresh_token'] == create_refresh_token({'sub': 'JohnDoe', 'scopes': None})
    assert data['token_type'] == 'bearer'


def test_upload_video():
    with open('test_videos/test.mp4', 'rb') as file:
        response = client.post('/upload_video/?video_title=test_video&video_description=test_description',
                               files={'file': ('test.mp4', file, 'video/mp4')}, headers={
                'User-Auth-Token': create_access_token({'sub': 'JohnDoe', 'scopes': ['admin']})})
        assert response.status_code == 200
        video = get_video_by_title('test_video')
        test_db.close()
        assert video.title == 'test_video'
        assert video.description == 'test_description'
        assert video.author == 'JohnDoe'


# def test_upload_same_video():
#     with open('test_videos/test.mp4', 'rb') as file:
#         response = client.post('/upload_video/?video_title=test_video&video_description=test_description',
#                                files={'file': ('test.mp4', file, 'video/mp4')}, headers={
#                 'User-Auth-Token': create_access_token({'sub': 'JohnDoe', 'scopes': ['admin']})})
#         assert response.status_code == 200
#         # print(response.json())
#         data = response.json()['error']
#         assert data['code'] == 2000
#         assert data['message'] == 'Video already exists'


def test_get_videos():
    response = client.post('/api', json=get_json_rpc_body('get_videos', {}))

    assert response.status_code == 200
    data = response.json()['result']
    assert data == [{'title': 'test_video',
                     'description': 'test_description',
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
        }
    }), headers={'User-Auth-Token': create_access_token({'sub': 'JohnDoe', 'scopes': ['admin']})})
    assert response.status_code == 200
    # history = get_history_by_id(1)
    # assert history.video_id == 1
    # assert history.timestamp == 14
    # assert history.date_visited == '2023-03-29T14:58:14.559Z'


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
