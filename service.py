import kopf
import time
import asyncio
import kubernetes
import os
import logging
from xlscsde.nhs.uk.secrets.distributor import SecretDistribution, SecretDistributionApi

group = "xlscsde.nhs.uk"
kind = "SecretsDistribution"
version = "v1"
api_version = f"{group}/{version}"

kube_config = {}

kubernetes_service_host = os.environ.get("KUBERNETES_SERVICE_HOST")
managed_by = os.environ.get("MANAGED_BY", "secrets-distributor")
secrets_path = os.environ.get("SECRETS_PATH", "/mnt/secrets")

if kubernetes_service_host:
    kube_config = kubernetes.config.load_incluster_config()
else:
    kube_config = kubernetes.config.load_kube_config()

api_client = kubernetes.client.ApiClient(kube_config)
core_api = kubernetes.client.CoreV1Api(api_client)
dynamic_client = kubernetes.dynamic.DynamicClient(api_client)
custom_api = dynamic_client.resources.get(api_version = api_version, kind = kind)

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.watching.connect_timeout = 60
    settings.watching.server_timeout = 60

@kopf.on.create(group=group, kind=kind)
@kopf.on.update(group=group, kind=kind)
@kopf.on.resume(group=group, kind=kind)
def secretUpdated(status, name, namespace, spec, **_):   
    try:
        print(f"{name} on {namespace} has been updated")
        
        distribution_api = SecretDistributionApi(core_api = core_api, custom_api = custom_api)
        definition = SecretDistribution(
            name = name, 
            namespace = namespace, 
            spec = spec,
            status = status, 
            managed_by = managed_by, 
            secrets_path = secrets_path,
            api = distribution_api
            )
        definition.updateTargetSecret()
    except Exception as e:
        logging.error(f"An unexpected error has occurred: {e}")
