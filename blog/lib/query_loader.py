import xml.etree.ElementTree as Et
import os


class QueryLoader(object):
    __instance = None

    def __init__(self, location=None):
        self.query_files_dict = {}
        self.load(location)

    def __new__(cls, location=None):
        if QueryLoader.__instance is None:
            QueryLoader.__instance = object.__new__(cls)
        return QueryLoader.__instance

    def load(self, location=None):
        if location is None:
            location = 'query_xml'

        file_names = os.listdir(location)
        for filename in file_names:
            src = '%s/%s' % (location, filename)
            tree = Et.parse(src)
            name = filename.split('.')[0]
            self.query_files_dict[name] = tree.getroot()

    def get_query(self, category, query_id):
        if category in self.query_files_dict:
            query_node = self.query_files_dict[category].find(".//query[@id='" + query_id + "']")

        return query_node.text

    def get_query_id_list(self):
        self.load()
        return self.query_files_dict
