import io
import urllib

import boto3
import math
import numpy
import tempfile

from PIL import Image
from flask import Flask, request, json
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
instance_id = 'W_' + instance_id

# S3 config
resource = boto3.resource('s3', region_name=REGION_NAME)
s3 = boto3.client('s3')

# SDB config
DOMAIN_NAME = 'photoapp'
sdb = SimpleDB(region_name=REGION_NAME, domain_name=DOMAIN_NAME, instance_id=instance_id)
sdb.create_domain_if_not_exist(DOMAIN_NAME)


@application.route('/')
def index():
	return 'PhotoApp processing unit'


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
	print(data)
	print(data["Bucket"])

	sdb.log([
		{'Name': 'Type', 'Value': 'Request started'},
		{'Name': 'Function', 'Value': 'process'},
		{'Name': 'Url', 'Value': request.url},
		{'Name': 'Data', 'Value': json.dumps(data)}
	])

	for image_info in data["Images"]:

		result_file = io.BytesIO()

		bucket = resource.Bucket(data["Bucket"])
		image_object = bucket.Object(image_info["Key"])
		image_data = image_object.get()['Body'].read()
		image = io.BytesIO(image_data)

		img = Image.open(image).convert('1')

		for i in range(15000000):
			math.sqrt(i) / math.sqrt(i + 50) * math.sqrt(i + i) / (i + 50)

		result_img = img.rotate(180)
		result_img.save(result_file, "JPEG")
		result_file.seek(0)

		

		response = s3.put_object(
			Bucket=data["Bucket"],
			Key=image_info["Key"],
			Body=result_file,
			ContentType='image/jpeg',
			ACL='public-read'
		)

		sdb.log([
			{'Name': 'Type', 'Value': 'Request finished'},
			{'Name': 'Function', 'Value': 'process'},
			{'Name': 'Url', 'Value': request.url},
			{'Name': 'Response', 'Value': json.dumps(response)}
		])

	return json.dumps(response), 200


if __name__ == "__main__":
	application.run(port=80)
