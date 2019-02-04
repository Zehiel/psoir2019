import urllib

import boto3
import datetime
from flask import Flask, render_template, request, json
from flask_cors import CORS

from simpledb import SimpleDB

application = Flask(__name__)
application.debug = True

CORS(application)

# config
REGION_NAME = 'us-west-2'

meta = 'http://169.254.169.254/latest/meta-data/instance-id'
instance_id = None
try:
	i_id = urllib.request.urlopen(meta).read()
	print('on EC2')
	instance_id = i_id.decode()
except:
	print('local dev')
	instance_id = 'local_dev'
instance_id = 'F_' + instance_id

# S3 config
BUCKET_NAME = 'psoir-photo-vault'
s3 = boto3.client('s3')

# SQS config
SQS_URL = 'https://sqs.us-west-2.amazonaws.com/057211213296/psoir-photo-queue'
sqs = boto3.client('sqs', region_name=REGION_NAME)

# SDB config
DOMAIN_NAME = 'photoapp'
sdb = SimpleDB(region_name=REGION_NAME, domain_name=DOMAIN_NAME, instance_id=instance_id)
sdb.create_domain_if_not_exist(DOMAIN_NAME)


@application.route('/')
def index():
	files = s3.list_objects_v2(Bucket=BUCKET_NAME)

	if files["KeyCount"] < 1:
		files["Contents"] = []

	return render_template('index.html', result=files["Contents"])


@application.route('/process', methods=['POST'])
def process():
	if request.json is None:
		sdb.log([
			{'Name': 'Type', 'Value': 'Request failed'},
			{'Name': 'Function', 'Value': 'process'},
			{'Name': 'Url', 'Value': request.url}
		])
		return "", 415

	data = request.get_json()

	sdb.log([
		{'Name': 'Type', 'Value': 'Request started'},
		{'Name': 'Function', 'Value': 'process'},
		{'Name': 'Url', 'Value': request.url},
		{'Name': 'Data', 'Value': json.dumps(data)}
	])

	for data_part in chunks(data, 1):
		msg = dict(Images=data_part, Bucket=BUCKET_NAME)
		print(json.dumps(msg))

		response = sqs.send_message(
			QueueUrl=SQS_URL,
			MessageBody=json.dumps(msg)
		)

		sdb.log([
			{'Name': 'Type', 'Value': 'Request sent'},
			{'Name': 'Function', 'Value': 'process'},
			{'Name': 'Url', 'Value': request.url},
			{'Name': 'Response', 'Value': json.dumps(response)}
		])

	return 'Request sent', 200


def chunks(l, n):
	"""Yield successive n-sized chunks from l."""
	for i in range(0, len(l), n):
		yield l[i:i + n]


if __name__ == '__main__':
	application.run(debug=True)
