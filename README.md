# Secrets Distributor
The secrets distributor effectively copies secrets that are exposed to it to destination secrets on the same or other namespaces as defined in a custom resource. This way you can get the secrets from a third party location such as key vault and have the same secrets exposed to multiple other projects without having to hook up each container to azure keyvault etc. This greatly simplifies implementation of secrets when supporting multiple providers.

 