#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
import ovh
import json
import datetime
import dateutil.parser
import os

def get_usage(client_ovh, project_id): 
  result=client_ovh.get('/cloud/project/'+project_id+'/usage/current')
  return result

def get_list_of_projects(client_ovh):
  result = client_ovh.get('/cloud/project')
  return result

def get_description_of_project(client_ovh, project_id):
  result = client_ovh.get('/cloud/project/'+project_id)
  if result['status']!="ok":
    description=None
  else:
    description = result['description'].replace(' ','_')
  return description

def get_client(endpoint, app_key, app_sec, cons_key):
  client_ovh = ovh.Client(
        endpoint=endpoint,               # Endpoint of API OVH Europe (List of available endpoints)
        application_key=app_key,    # Application Key
        application_secret=app_sec, # Application Secret
        consumer_key=cons_key,       # Consumer Key
    ) 
  return client_ovh

def format_usage(project, project_name, current_usage):
  result=[]
  measurement_name_cost='ovhcloud_publiccloud_usage'
  begin_line='{} project_id={},project_name={}'.format(measurement_name_cost,project,project_name)

  # influxdb expects nanosecond epoch time
  last_update=dateutil.parser.parse(current_usage['lastUpdate']).timestamp()*1000*1000*1000

  schema={
    'hourlyUsage': {
        'instance':{'tags': ['reference', 'region'], 'field':['totalPrice']},
        'instanceBandwidth':{'tags': ['region'], 'field':['totalPrice']},
        'instanceOption':{'tags': ['reference', 'region'], 'field':['totalPrice']},
        'snapshot':{'tags': ['region'],'field':['totalPrice']},
        'storage':{'tags': ['bucketName', 'region'], 'field':['totalPrice']},
        'volume':{'tags': ['type', 'region'], 'field':['totalPrice']}
    },
    'monthlyUsage': {
      'instance':{'tags': ['reference', 'region'], 'field':['totalPrice']},
      'instanceOption':{'tags': ['reference', 'region'], 'field':['totalPrice']},
      'certification':{'tags': ['reference'], 'field':['totalPrice']}
      },
    'resourcesUsage':[{'tags': ['type'], 'field':['totalPrice']}]
  }

  for schema_key, schema_value in schema.items():
    a=current_usage[schema_key]
    if a is None:
      pass
    elif type(schema_value) is dict:
      for schema_subkey, schema_subvalue in schema_value.items():
        b=a[schema_subkey]
        for c in b:
          point=begin_line+',category={}'.format(schema_key)
          for one_value in schema_subvalue['field']:
            for tag in schema_subvalue['tags']:
              if c[tag]!="":
                point+=',{}={}'.format(tag, c[tag])
            if one_value in c:
              point+=' {}={}'.format(one_value, c[one_value])
              point+=' {:.0f}'.format(last_update)
              result.append(point)
    elif type(schema_value) is list:
        for ressource in a:
          point=begin_line+',category={}'.format(schema_key)
          for one_value in schema_value[0]['field']:
            for tag in schema_value[0]['tags']:
              point+=',{}={}'.format(tag, ressource[tag])
            if one_value in ressource:
              point+=' {}={}'.format(one_value, ressource[one_value])
              point+=' {:.0f}'.format(last_update)
              result.append(point)
  return result

def main():
  endpoint=os.environ['OVH_ENDPOINT']              # endpoint
  application_key=os.environ['OVH_APP_KEY']       # Application Key
  application_secret=os.environ['OVH_APP_SECRET'] # Application Secret
  consumer_key=os.environ['OVH_CONSUMER_KEY']     # Consumer Key

  client_ovh=get_client(endpoint, application_key, application_secret, consumer_key)
  projects=get_list_of_projects(client_ovh)
  
  for project in projects:
    project_description=get_description_of_project(client_ovh, project)
    if project_description is None:
      pass
    else:
      usage=get_usage(client_ovh, project)
      result=format_usage(project,project_description, usage)
      for i in result:
        print(i)

if __name__ == '__main__':
  main()
