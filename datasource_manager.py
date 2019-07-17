import requests
import logging
from other.exceptions import BrokerError

logger = logging.getLogger('semanticenrichment')

class Subscription:
    def __init__(self, subid, host, port, subscription):
        self.id = subid
        self.host = host
        self.port = port
        self.subscription = subscription


class DataSource:
    def __init__(self, dsid, dstype, metadata):
        self.id = dsid
        self.dstype = dstype
        self.metadata = metadata

    def update(self, metadata):
        self.metadata.update(metadata)



class DatasourceManager:

    def __init__(self):
        self.subscriptions = {}
        self.datasources = {}
        self.known_ngsi_hosts = [{"host": "http://155.54.95.248", "port": 9090}]

        self.headers = {}
        self.headers.update({'content-type': 'application/ld+json'})
        self.headers.update({'accept': 'application/ld+json'})
        self.get_active_subscriptions()

    def add_subscription(self, host, port, subscription):
        # subscribe to ngsi-ld endpoint
        sub = Subscription(subscription['id'], host, port, subscription)

        server_url = host + ":" + str(port) + "/ngsi-ld/v1/subscriptions/"
        r = requests.post(server_url, json=subscription, headers=self.headers)
        logger.info("Adding subscription: " + r.text)
        if r.status_code == 500:
            logger.debug("error creating subscription: " + r.text)
            raise BrokerError(r.text)
        else:
            self.subscriptions[sub.id] = sub
        return r.text

    def del_subscription(self, subid):
        subscription = self.subscriptions.pop(subid)

        server_url = subscription.host + ":" + str(subscription.port) + "/ngsi-ld/v1/subscriptions/"
        server_url = server_url + subid
        r = requests.delete(server_url, headers=self.headers)
        logger.debug("deleting subscription " + subid + ": " + r.text)

    def add_datasource(self, data):
        # check if datasource is already registered, if so update metadata
        dsid = data['id']
        if dsid in self.datasources:
            self.datasources[dsid].update(data)
        else:
            datasource = DataSource(dsid, data['type'], data)
            self.datasources[dsid] = datasource
        # TODO check how to get the data
        # in testing we always receive data and metadata in one ngsi-ld form automatically
        # TODO later to send data "request" to data handler in monitoring

    def get_subscriptions(self):
        return self.subscriptions

    def get_datasources(self):
        return self.datasources

    # TODO this method is mainly for testing etc as subscriptions are lost during restart,
    # in addition ngrok won't fit for old subscriptions
    def get_active_subscriptions(self):
        for host in self.known_ngsi_hosts:
            # get old subscriptions for semantic enrichment (starting with 'SE_')
            server_url = host['host'] + ":" + str(host['port']) + "/ngsi-ld/v1/subscriptions/"
            r = requests.get(server_url, headers=self.headers)
            ids = ()
            if r.status_code != 500:
                for data in r.json():
                    if data['id'].startswith('SE_', data['id'].rfind(':') + 1):
                        sub = Subscription(data['id'], host['host'], host['port'], data)
                        self.subscriptions[sub.id] = sub
            else:
                logger.error("Error getting active subscriptions: " + r.text)
            return ids
