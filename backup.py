import requests
import boto3
import time
import os
import base64
import sys
import io

ACCOUNT_NAME = os.environ['ACCOUNT_NAME']
ACCOUNT_PASSWORD = os.environ['ACCOUNT_PASSWORD']
BUCKET_NAME = os.environ['BUCKET_NAME']

s3 = boto3.client('s3')
basic_auth = base64.b64encode(f'{ACCOUNT_NAME}:{ACCOUNT_PASSWORD}'.encode()).decode("utf-8") 

def log(message):
  print('{"date": "' + time.strftime("%Y-%m-%d %H:%M") + '", "message": "' + message + '"')

def get_branches(repository, username):
  request = requests.get(f'https://api.bitbucket.org/2.0/repositories/{username}/{repository}/refs/branches', headers={'Authorization': f'Basic {basic_auth}'})
  if (request.status_code == 200):
    return request.json()['values']
  else:
    log(f'failed getting branches from repository {repository} from {username}, response:{str(request.text)}')
    return []

def backup(branch_name, repository, username):
  log(f'backup branch {branch_name} from repository {repository} from {username}')
  response = requests.get(f'https://bitbucket.org/{username}/{repository}/get/{branch_name}.zip', headers={'Authorization': f'Basic {basic_auth}'}, stream=True)
  if (response.status_code == 200):
    filename = f'{username}-{repository}/{branch_name.replace("/","-")}.zip'
    s3.upload_fileobj(io.BytesIO(response.content), BUCKET_NAME, filename)
  else:
    log(f'failed getting zip of branch {branch_name} from repository {repository} from {username}, response:{str(response.text)}')

def get_repositories():
  page = f'https://api.bitbucket.org/2.0/repositories?role=member'
  repositories = []
  while True:
    request = requests.get(page, headers={'Authorization': f'Basic {basic_auth}'})
    if (request.status_code == 200):
      json = request.json()
      for repo in json['values']:
        owner = repo['owner']
        if 'username' in owner:
          username = owner['username']
        else:
          username = owner['nickname']
        repository = repo['name'].replace(' ', '-')
        repositories.append((repository, username))
      if 'next' in json:
        page = json['next']
      else: 
        break
    else:
      log(f'failed getting account information, response:{str(request.text)}')
      sys.exit(1)
  return repositories

for repository,username in get_repositories():
  branches = get_branches(repository, username)
  for branch in branches:
    branch_name = branch['name']
    backup(branch_name, repository, username)