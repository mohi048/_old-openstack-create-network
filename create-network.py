#!/usr/bin/python

from neutronclient.v2_0 import client
from configparser import SafeConfigParser
import requests
import time
sleep_time = 0
parser = SafeConfigParser()
if parser.read('./config.ini') != []:
    pass
else:
    raise IOError("Could not read config.ini file on base directory")

credentials = {}
credentials['username'] =  parser.get('ACCOUNT_CREDENTIALS', 'OS_USERNAME')
credentials['password'] =  parser.get('ACCOUNT_CREDENTIALS', 'OS_PASSWORD')
credentials['tenant_name'] =  parser.get('ACCOUNT_CREDENTIALS', 'OS_TENANT_NAME')
credentials['auth_url'] =  parser.get('ACCOUNT_CREDENTIALS', 'OS_AUTH_URL')

try:
    print "\n Attempting to connect on %s" %credentials['auth_url']
    response = requests.get(url=credentials['auth_url'],timeout=(10.0,1))
except requests.exceptions.ReadTimeout as e:
    print e.message
finally:
    print "Connected to the host"



neutron = client.Client(**credentials)

### Creating Private Network

try:
    print('Attempting to create network  :: %s \n' %parser.get('PRIVATE_NETWORK_DETAILS','NETWORK_NAME'))
    body_sample = {'network': {'name': parser.get('PRIVATE_NETWORK_DETAILS','NETWORK_NAME'),'admin_state_up': True,'shared':False,'provider:network_type': 'local'}}
    netw = neutron.create_network(body=body_sample)
    net_dict = netw['network']
    private_network_id = net_dict['id']
    print('Network created :: %s \n' %parser.get('PRIVATE_NETWORK_DETAILS','NETWORK_NAME'))
    time.sleep(sleep_time)
    print ("Creating Subnet :: %s \n" %parser.get('PRIVATE_NETWORK_DETAILS','SUBNET_NAME' ))
    body_create_subnet = {'subnets': 
    						[{'cidr': parser.get('PRIVATE_NETWORK_DETAILS','NETWORK_RANGE'),
                                'name': parser.get('PRIVATE_NETWORK_DETAILS','SUBNET_NAME'),
    						  'ip_version': parser.get('PRIVATE_NETWORK_DETAILS','IP_VERSION'),
    						   'network_id': private_network_id,
                               'gateway_ip': parser.get('PRIVATE_NETWORK_DETAILS','IP_POOL_GATEWAY'),
    						   'dns_nameservers':[parser.get('PRIVATE_NETWORK_DETAILS','DNS_SERVERS')],
    						   'allocation_pools': [{'start': parser.get('PRIVATE_NETWORK_DETAILS','IP_POOL_START'), 'end': parser.get('PRIVATE_NETWORK_DETAILS','IP_POOL_END')}], 
    						   }]}

    private_subnet = neutron.create_subnet(body=body_create_subnet)
    print('Created Subnet :: %s \n' %parser.get('PRIVATE_NETWORK_DETAILS','SUBNET_NAME' ) )
    print('Listing the network details :: %s\n' %parser.get('PRIVATE_NETWORK_DETAILS','NETWORK_NAME'))
    time.sleep(sleep_time)
    for key,values in net_dict.iteritems():
        print str(key) + " :: " + str(values)
    
    print('\nListing Subnet details :: %s \n' %parser.get('PRIVATE_NETWORK_DETAILS','SUBNET_NAME' ) )
    Priv_subnet = neutron.list_subnets(network_id = private_network_id)['subnets'][0]
    time.sleep(sleep_time)
    for key,values in Priv_subnet.iteritems():
        print str(key) + " :: " + str(values)
finally:
    time.sleep(sleep_time)
    print("Network %s and subnet %s created, Execution completed \n" %(parser.get('PRIVATE_NETWORK_DETAILS','NETWORK_NAME'),parser.get('PRIVATE_NETWORK_DETAILS','SUBNET_NAME' )))




### Creating Public Network
try:
    if parser.has_option('PUBLIC_NETWORK_DETAILS', 'ID'):
        public_network_id = parser.get('PUBLIC_NETWORK_DETAILS', 'ID')
        time.sleep(sleep_time)
        print "\n Skipping the creating of public network and using the existing network id %s" %public_network_id
    else:
        time.sleep(sleep_time)
        print ("Creating new network :: %s \n" %parser.get('PUBLIC_NETWORK_DETAILS','NETWORK_NAME'))
        body_sample = {'network': {'name': parser.get('PUBLIC_NETWORK_DETAILS','NETWORK_NAME'),'admin_state_up': True,'shared':parser.get('PUBLIC_NETWORK_DETAILS','SHARED'),'router:external':True,
            'provider:network_type': parser.get('PUBLIC_NETWORK_DETAILS','PROVIDER_NETWORK_TYPE'),
            'provider:physical_network' : parser.get('PUBLIC_NETWORK_DETAILS','PROVIDER_PHYSICAL_NETWORK'),
            'provider:segmentation_id' : parser.get('PUBLIC_NETWORK_DETAILS','PROVIDER_SEGEMENTATION_ID')
            }}
        netw = neutron.create_network(body=body_sample)
        net_dict = netw['network']
        public_network_id = net_dict['id']
        time.sleep(sleep_time)
        for key,values in net_dict.iteritems():
            print str(key) + " :: " + str(values)
    time.sleep(sleep_time)
    print ("Attempting to create subnet :: %s\n" %parser.get('PUBLIC_NETWORK_DETAILS','SUBNET_NAME'))
    body_create_subnet = {'subnets': 
                            [{'cidr': parser.get('PUBLIC_NETWORK_DETAILS','NETWORK_RANGE'),
                                'name': parser.get('PUBLIC_NETWORK_DETAILS','SUBNET_NAME'),
                              'ip_version': parser.get('PUBLIC_NETWORK_DETAILS','IP_VERSION'),
                               'network_id': public_network_id,
                               'gateway_ip': parser.get('PUBLIC_NETWORK_DETAILS','IP_POOL_GATEWAY'),
                               'dns_nameservers':[parser.get('PUBLIC_NETWORK_DETAILS','DNS_SERVERS')],
                               'allocation_pools': [{'start': parser.get('PUBLIC_NETWORK_DETAILS','IP_POOL_START'), 'end': parser.get('PUBLIC_NETWORK_DETAILS','IP_POOL_END')}], 
                               'enable_dhcp':False,
                               }]
                            }

    public_subnet = neutron.create_subnet(body=body_create_subnet)
    time.sleep(sleep_time)
    print('Created subnet :: %s\n' %parser.get('PUBLIC_NETWORK_DETAILS','SUBNET_NAME'))
finally:
    print("%snetwork and %s subnet created, Execution completed\n" %((parser.get('PUBLIC_NETWORK_DETAILS','NETWORK_NAME')), parser.get('PUBLIC_NETWORK_DETAILS','SUBNET_NAME')))



#### Creating router

try:
    time.sleep(sleep_time)
    print ("Creating the Router:: %s" %parser.get('ROUTER_DETAILS','NAME'))
    request = {'router': {
                            'name': parser.get('ROUTER_DETAILS','NAME'),
                            'admin_state_up': True,
                            'external_gateway_info': 
                            {
                            'network_id':public_network_id,
                            'enable_snat':'True'
                            }
                            }}
    router = neutron.create_router(request)
    router_id = router['router']['id']
    router = neutron.show_router(router_id)
    neutron.add_interface_router(router_id, { 'subnet_id' : Priv_subnet['id'] } )
    
finally:
    print("Router created\n")

