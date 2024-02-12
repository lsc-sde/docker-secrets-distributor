from distributor import SecretDistribution
import kubernetes
import unittest
import logging

class TestSecretDistribution(unittest.TestCase):
    def setUp(self):
        logging.getLogger().setLevel(logging.DEBUG)
        self.distributor = SecretDistribution(name = "test", namespace = "test", managed_by = "test", secrets_path = "/mnt/secrets")
        self.distributor.target_secret = kubernetes.client.V1Secret(
            metadata = kubernetes.client.V1ObjectMeta(
                annotations={
                    "xlscsde.nhs.uk/managedBy" : "test"
                }
            ),
            data = {
                "testName" : "testValue"
            }
        )
        self.distributor.secret_definition = kubernetes.client.V1Secret(
            metadata = kubernetes.client.V1ObjectMeta(
                annotations={
                    "xlscsde.nhs.uk/managedBy" : "test"
                }
            ),
            data = {
                "testName" : "testValue"
            }
        )

    def test_compare_same(self):
        self.assertFalse(self.distributor.secretsAreDifferent())

    def test_compare_different_value(self):
        self.distributor.target_secret.data["testName"] = "testValue2"
        self.assertTrue(self.distributor.secretsAreDifferent())

    def test_compare_additional_value_on_target(self):
        self.distributor.target_secret.data["testName2"] = "testValue2"
        self.assertTrue(self.distributor.secretsAreDifferent())

    def test_compare_additional_value_on_definition(self):
        self.distributor.secret_definition.data["testName2"] = "testValue2"
        self.assertTrue(self.distributor.secretsAreDifferent())

        

if __name__ == '__main__':
    unittest.main()