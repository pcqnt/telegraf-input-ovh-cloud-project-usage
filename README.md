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
ovhcloud_publiccloud_usage,project_id=abcd,project_name=My_Project,category=hourlyUsage,reference=d2-2,region=SBG7 totalPrice=0.823 1682155111041499904
ovhcloud_publiccloud_usage,project_id=abcd,project_name=My_Project,category=hourlyUsage,bucketName=s3-bucketname,region=GRA totalPrice=0.9 1682155111041499904
ovhcloud_publiccloud_usage,project_id=defg,project_name=My_Project_2,category=hourlyUsage,reference=b2-15,region=SBG5 totalPrice=66.048 1682155079677974016
ovhcloud_publiccloud_usage,project_id=defg,project_name=My_Project_2,category=hourlyUsage,reference=b2-7,region=SBG5 totalPrice=34.867 1682155079677974016
ovhcloud_publiccloud_usage,project_id=defg,project_name=My_Project_2,category=hourlyUsage,region=BHS3 totalPrice=0.321 1682155079677974016
ovhcloud_publiccloud_usage,project_id=defg,project_name=My_Project_2,category=hourlyUsage,region=SBG5 totalPrice=0.75 1682155079677974016
ovhcloud_publiccloud_usage,project_id=defg,project_name=My_Project_2,category=hourlyUsage,region=GRA totalPrice=0 1682155079677974016
ovhcloud_publiccloud_usage,project_id=defg,project_name=My_Project_2,category=resourcesUsage,type=gateway totalPrice=1.439 1682154979129154048
ovhcloud_publiccloud_usage,project_id=defg,project_name=My_Project_2,category=monthlyUsage,reference=win-b2-15,region=SBG5 totalPrice=86.2 1682154665347398912


```
