import os
from boto.ec2.connection import EC2Connection
from boto.ec2.regioninfo import RegionInfo
#from datetime import datetime, timedelta
import datetime
from datetime import datetime, timedelta
import time
import sys
import logging
from config import config
ts = time.time()

st = datetime.today().strftime('%Y-%m-%d' '/' '%H:%M:%S')
print st
if (len(sys.argv) < 2):
    print('Please add a positional argument: day, week or month.')
    quit()
else:
    if sys.argv[1] == 'day':
        period = 'day'
        date_suffix = datetime.today().strftime('%a')
    elif sys.argv[1] == 'week':
        period = 'week'
        date_suffix = datetime.today().strftime('%U')
    elif sys.argv[1] == 'month':
        period = 'month'
        date_suffix = datetime.today().strftime('%b')
    else:
        print('Please use the parameter day, week or month')
        quit()

# Counters
total_creates = 0
total_deletes = 0
count_errors = 0

# List with snapshots to delete
deletelist = []

# Setup logging
logging.basicConfig(filename=config['log_file'], level=logging.INFO)
start_message = 'Started taking %(period)s snapshots at %(date)s' % {
    'period': period,
    'date': datetime.today().strftime('%d-%m-%Y %H:%M:%S')
}

# Get settings from config.py
aws_access_key = config['aws_access_key']
aws_secret_key = config['aws_secret_key']
ec2_region_name = config['ec2_region_name']
ec2_region_endpoint = config['ec2_region_endpoint']
sns_arn = config.get('arn')
proxyHost = config.get('proxyHost')
proxyPort = config.get('proxyPort')

region = RegionInfo(name=ec2_region_name, endpoint=ec2_region_endpoint)

# Number of snapshots to keep
keep_week = config['keep_week']
keep_day = config['keep_day']
keep_month = config['keep_month']
count_success = 0
count_total = 0

# Connect to AWS using the credentials provided above or in Environment vars or using IAM role.
print 'Connecting to AWS'
if proxyHost:
    # proxy:
    # using roles
    if aws_access_key:
        conn = EC2Connection(aws_access_key, aws_secret_key, region=region, proxy=proxyHost, proxy_port=proxyPort)
    else:
        conn = EC2Connection(region=region, proxy=proxyHost, proxy_port=proxyPort)
else:
    # non proxy:
    # using roles
    if aws_access_key:
        conn = EC2Connection(aws_access_key, aws_secret_key, region=region)
    else:
        conn = EC2Connection(region=region)

def get_resource_tags(resource_id):
    resource_tags = {}
    if resource_id:
        tags = conn.get_all_tags({ 'resource-id': resource_id })
        for tag in tags:
            # Tags starting with 'aws:' are reserved for internal use
            if not tag.name.startswith('aws:'):
                resource_tags[tag.name] = tag.value
    return resource_tags

def set_resource_tags(resource, tags):
    for tag_key, tag_value in tags.iteritems():
        if tag_key not in resource.tags or resource.tags[tag_key] != tag_value:
            print 'Tagging %(resource_id)s with [%(tag_key)s: %(tag_value)s]' % {
                'resource_id': resource.id,
                'tag_key': tag_key,
                'tag_value': tag_value
            }
            resource.add_tag(tag_key, tag_value)

# Get all the volumes that match the tag criteria
print 'Finding volumes that match the requested tag ({ "tag:%(tag_name)s": "%(tag_value)s" })' % config
vols = conn.get_all_volumes(filters={ 'tag:' + config['tag_name']: config['tag_value'] })

for vol in vols:
    try:
        count_total += 1
        logging.info(vol)
        tags_volume = get_resource_tags(vol.id)
        description = '%(period)s_snapshot %(vol_id)s_%(period)s_%(date_suffix)s by snapshot script at %(date)s' % {
            'period': period,
            'vol_id': vol.id,
            'date_suffix': date_suffix,
            'date': datetime.today().strftime('%d-%m-%Y %H:%M:%S')
        }
        try:
            tags_volume['Name'] = 'Snap-' + st ;
            print tags_volume
            current_snap = vol.create_snapshot(description)
            set_resource_tags(current_snap, tags_volume)
            suc_message = 'Snapshot created with description: %s and tags: %s' % (description, str(tags_volume))
            print '     ' + suc_message
            logging.info(suc_message)
            total_creates += 1
        except Exception, e:
            print "Unexpected error:", sys.exc_info()[0]
            logging.error(e)
            pass

#        snapshots = vol.snapshots()
#        deletelist = []
#        for snap in snapshots:
#            sndesc = snap.description
#            if (sndesc.startswith('week_snapshot') and period == 'week'):
#                deletelist.append(snap)
#            elif (sndesc.startswith('day_snapshot') and period == 'day'):
#                deletelist.append(snap)
#            elif (sndesc.startswith('month_snapshot') and period == 'month'):
#                deletelist.append(snap)
#            else:
#                logging.info('     Skipping, not added to deletelist: ' + sndesc)

        for snap in deletelist:
            logging.info(snap)
            logging.info(snap.start_time)

        def date_compare(snap1, snap2):
            if snap1.start_time < snap2.start_time:
                return -1
            elif snap1.start_time == snap2.start_time:
                return 0
            return 1

        deletelist.sort(date_compare)
        if period == 'day':
            keep = keep_day
        elif period == 'week':
            keep = keep_week
        elif period == 'month':
            keep = keep_month
        delta = len(deletelist) - keep
        for i in range(delta):
            del_message = '     Deleting snapshot ' + deletelist[i].description
            logging.info(del_message)
            deletelist[i].delete()
            total_deletes += 1
        time.sleep(3)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        logging.error('Error in processing volume with id: ' + vol.id)
        errmsg += 'Error in processing volume with id: ' + vol.id
        count_errors += 1
    else:
        count_success += 1

result = '\nFinished making snapshots at %(date)s with %(count_success)s snapshots of %(count_total)s possible.\n\n' % {
    'date': datetime.today().strftime('%d-%m-%Y %H:%M:%S'),
    'count_success': count_success,
    'count_total': count_total
}
logging.info(result)


# Deleting Snapshot
#
#try:
#	days 
# = int(sys.argv[1])
#except IndexError:
#	days = 7
#
#delete_time = datetime.utcnow() - timedelta(days=days)
#
#filters = {
#	'tag-key': 'mybackups'
#}
#
#print 'Deleting any snapshots older than {days} days'.format(days=days)
#
#ec2 = connect_to_region('us-west-1')
#
#snapshots = ec2.get_all_snapshots(filters=filters)
#
#deletion_counter = 0
#size_counter = 0

