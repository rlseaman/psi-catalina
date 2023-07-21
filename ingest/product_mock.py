class ProductMock:
    """
    Represents the product itself.
    """

    def __init__(self, datapath, filename, inst, year, date):
        """
        Parses a label file into a Product
        """
        self.keywords = {
            "collection_id":"data",
            "lidvid":"urn:nasa:pds:catalina:data:" + filename,
            "file_name":filename
        }
        self.inst = inst
        self.year = year
        self.date = date
        self.labelfilename = filename
