# telegraf-input-ovh-cloud-project-usage
Python script to parse the output of [OVHcloud Public Cloud Project Usage](https://api.ovh.com/console/#/cloud/project/%7BserviceName%7D/usage/current~GET) into the [InfluxDB line protocol](https://docs.influxdata.com/influxdb/latest/reference/syntax/line-protocol/). Intended to be run via Telegraf's [exec](https://github.com/influxdata/telegraf/tree/master/plugins/inputs/exec) input plugin.

## Requirements
OVHcloud Python module (pip install ovh)

## Install
Configure Telegraf as shown below. Make sure to have the following environnement variables set:
```
OVH_APP_KEY
OVH_ENDPOINT=ovh-eu
OVH_APP_SECRET
OVH_CONSUMER_KEY
```
Alternatively you can build a docker container with the provided Dockerfile

## Configuration

`/etc/telegraf/telegraf.conf`
```
[[inputs.exec]]
   commands = ["python3 /usr/src/app/ovh-pci-cost.py"]
   data_format = "influx"
   interval = "2h"
   timeout = "300s"

```

## Sample output
```
$ python3 ./ovh-pci-cost.py 
ovhcloud_publiccloud_usage,project_id=abc,project_name=My_Project,category=hourlyUsage,subcategory=storage,bucketName=highperf-s3,region=SBG totalPrice=0 1683641700855802112
ovhcloud_publiccloud_usage,project_id=abc,project_name=My_Project,category=hourlyUsage,subcategory=storage,bucketName=s3-standard-gra,region=GRA totalPrice=0 1683641700855802112
ovhcloud_publiccloud_usage,project_id=abc,project_name=My_Project,category=hourlyUsage,subcategory=storage,bucketName=s3-standard-gra-logs,region=GRA totalPrice=0 1683641700855802112
ovhcloud_publiccloud_usage,project_id=abc,project_name=My_Project,category=hourlyUsage,subcategory=storage,bucketName=s3-locked,region=GRA totalPrice=0 1683641700855802112
ovhcloud_publiccloud_usage,project_id=abc,project_name=My_Project,category=hourlyUsage,subcategory=storage,bucketName=s3-objectlock,region=GRA totalPrice=0 1683641700855802112
ovhcloud_publiccloud_usage,project_id=abc,project_name=My_Project,category=hourlyUsage,subcategory=storage,bucketName=s3-s3fs-rbx,region=RBX totalPrice=0 1683641700855802112
ovhcloud_publiccloud_usage,project_id=def,project_name=My_Other_Project,category=hourlyUsage,subcategory=instance,reference=b2-15,region=SBG5 totalPrice=26.574 1683645236635727104
ovhcloud_publiccloud_usage,project_id=def,project_name=My_Other_Project,category=hourlyUsage,subcategory=instance,reference=b2-7,region=SBG5 totalPrice=14.029 1683645236635727104
ovhcloud_publiccloud_usage,project_id=def,project_name=My_Other_Project,category=hourlyUsage,subcategory=snapshot,region=BHS3 totalPrice=0.129 1683645236635727104
ovhcloud_publiccloud_usage,project_id=def,project_name=My_Other_Project,category=hourlyUsage,subcategory=snapshot,region=GRA5 totalPrice=0.306 1683645236635727104


```
