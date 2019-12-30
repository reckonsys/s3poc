import hmac
from os import environ

from boto3.session import Session, Config
from bottle import route, run, template, request, post

# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html#generating-a-presigned-url-to-upload-a-file  # noqa: E501
BUCKET_NAME = environ['BUCKET_NAME']
BUCKET_REGION = environ['BUCKET_REGION']
AWS_ACCESS_KEY_ID = environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = environ['AWS_SECRET_ACCESS_KEY']

session = Session(region_name=BUCKET_REGION)
s3 = session.client(
    's3', aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    config=Config(signature_version='s3v4'),
)


def get_digest(msg):
    result = hmac.new(
        AWS_SECRET_ACCESS_KEY.encode('utf-8'), msg=msg.encode('utf-8'))
    return result.hexdigest()


def verify_digest(key, digest):
    """Verify the giben digest."""
    return hmac.compare_digest(digest, get_digest(key))


def create_presigned_post(key, expiration=3600):
    return s3.generate_presigned_post(BUCKET_NAME, key, ExpiresIn=expiration)


@route('/')
def index():
    with open('index.html') as f:
        return template(f.read())


@route('/presigned')
def presigned():
    key = 'foo'
    data = create_presigned_post(key)
    data['hmac'] = get_digest(key)
    return data


@post('/uploaded')
def uploaded():
    key = request.json['key']
    hmac = request.json['hmac']
    if verify_digest(key, hmac):
        return {'success': True, 'message': 'Valid'}
    return {'success': False, 'message': 'Invalid'}


@route('/hello/<name>')
def hello(name):
    return template('<b>Hello {{name}}</b>!', name=name)


if __name__ == '__main__':
    run(host='localhost', port=8080)
