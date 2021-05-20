

class ADAPIException(Exception):
    """
    Custom API exception
    """

    def __init__(self, err, status_code=None):
        super(ADAPIException, self).__init__(err)
        self.status_code = status_code
