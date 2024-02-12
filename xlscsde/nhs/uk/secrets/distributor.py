import os
import base64 
import logging
import kubernetes

class SecretNotFoundException(Exception):
    def __init__(self, secret_name):
        self.secret_name = secret_name
        self.message = f"Secret {secret_name} was not found"
        super().__init__(self.message)

class SecretNotManagedByServiceException(Exception):
    def __init__(self, secret_name, is_managed_by, should_be_managed_by):
        self.secret_name = secret_name
        self.managed_by = is_managed_by
        self.message = f"Secret {secret_name} is managed by '{self.managed_by}' not '{should_be_managed_by}'"
        super().__init__(self.message)

class SecretDistribution:
    def __init__(self, name, namespace, managed_by, secrets_path, api = None, spec = None, status = None):
        self.name = name
        self.namespace = namespace
        if spec:
            self.spec = SecretDistributionSpec(spec)
        else:
            self.spec = SecretDistributionSpec()

        if status:
            self.status = SecretDistributionStatus(status)
        else:
            self.status = SecretDistributionStatus()

        self.managed_by = managed_by
        self.secrets_path = secrets_path
        self.api : SecretDistributionApi = api

    def convertToBase64(self, originalValue):
        originalValue_bytes = originalValue.encode("ascii") 
    
        base64_bytes = base64.b64encode(originalValue_bytes) 
        return base64_bytes.decode("ascii")
    
    def getSecretData(self):
        data = {}
        for secret in self.spec.secrets:
            file_name = f"{self.secrets_path}/{secret.copy_from}"
            if not os.path.isfile(file_name) and not os.path.islink(file_name):
                raise SecretNotFoundException(secret.copy_from)

            with open(file_name) as f:
                file_contents = f.read()
                data[secret.copy_to] = self.convertToBase64(file_contents)
        
        return data
            
    def buildSecretDefinition(self):
        return kubernetes.client.V1Secret(
            metadata=kubernetes.client.V1ObjectMeta(
                name = self.spec.name,
                namespace = self.namespace,
                annotations = {
                    "xlscsde.nhs.uk/managedBy" : self.managed_by
                }
            ),
            type=self.spec.type,
            data=self.getSecretData()
        )

    def getTargetSecret(self) -> kubernetes.client.V1Secret:
        secrets : kubernetes.client.V1SecretList
        secrets = self.api.core.list_namespaced_secret(namespace=self.namespace)
        
        secret: kubernetes.client.V1Secret 
        for secret in secrets.items:
            if secret.metadata.name.casefold() == self.spec.name.casefold():
                return secret
        
        return None
    
    def secretsAreDifferent(self):
        if self.target_secret: 
            target_secret_managed_by = self.target_secret.metadata.annotations.get("xlscsde.nhs.uk/managedBy")
            if not target_secret_managed_by:
                raise SecretNotManagedByServiceException(secret_name=self.spec.name, is_managed_by="")

            if target_secret_managed_by != self.managed_by:
                raise SecretNotManagedByServiceException(secret_name=self.spec.name, is_managed_by=target_secret_managed_by)
            
            definition_keys = self.secret_definition.data.keys()
            target_keys = self.target_secret.data.keys()
            added_keys = definition_keys - target_keys
            removed_keys = target_keys - definition_keys
            
            if len(added_keys) > 0:
                logging.debug(f"The following keys have been added: {added_keys}")
                return True
            
            if len(removed_keys) > 0:
                logging.debug(f"The following keys have been removed: {removed_keys}")
                return True;
        
            for key in target_keys:
                if self.secret_definition.data[key] != self.target_secret.data[key]:
                    logging.debug(f"'{key}' has changed")
                    return True

            return False
        return True

    def updateTargetSecret(self):
        self.target_secret = self.getTargetSecret()
        self.secret_definition = self.buildSecretDefinition()
        if self.secretsAreDifferent():
            if not self.target_secret:
                logging.info(f"Creating object {self.spec.name} on {self.namespace}")
                self.api.core.create_namespaced_secret(self.namespace, self.secret_definition)
            else:
                logging.info(f"Replacing object {self.spec.name} on {self.namespace}")
                self.api.core.replace_namespaced_secret(self.spec.name, self.namespace, self.secret_definition)
        else:
            logging.info(f"Object {self.spec.name} on {self.namespace} does not need updating")


class SecretDistributionStatus:
    def __init__(self, status = None):
        if status:
            self.status_text = status.get("statusText")
            self.last_updated = status.get("lastUpdated")
        else:
            self.status_text = ""
            self.last_updated = ""

class SecretDistributionSpecSecret:
    def __init__(self, secret):
        self.copy_from = secret.get("from")
        self.copy_to = secret.get("to")

class SecretDistributionApi:
    def __init__(self, core_api, custom_api):
        self.core : kubernetes.client.CoreV1Api = core_api
        self.custom = custom_api

class SecretDistributionSpec:
    def __init__(self, spec = None):
        if spec:
            self.name = spec.get("name")
            self.type = spec.get("type", "Opaque")
            secrets = spec.get("secrets", [])
            formatted_secrets = []
            for secret in secrets:
                formatted_secrets.append(SecretDistributionSpecSecret(secret))
            self.secrets = formatted_secrets
        else:
            self.name = ""
            self.type = "Opaque"
            self.secrets = []