import configparser

config = configparser.ConfigParser()
config.read('Configuration\\config.ini')


class readConfig():
    @staticmethod
    def getAwsBucketName():
        bucket_name = config.get('USER-DETAILS', 'aws_bucket_name')
        return bucket_name

    @staticmethod
    def getUserEmail():
        username = config.get('USER-DETAILS', 'gmail_username')
        return username

    @staticmethod
    def getPassword():
        password = config.get('USER-DETAILS', 'gmail_password')
        return password
    @staticmethod
    def getAwsAccessKey():
        access_key = config.get('USER-DETAILS', 'aws_access_key')
        return access_key
    @staticmethod
    def getAwasSecretAccessKey():
        secret_key = config.get('USER-DETAILS', 'aws_secret_access')
        return secret_key
