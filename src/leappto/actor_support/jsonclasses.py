""" Generate classes automatically based on JSON """

import json
import logging
import os
from jsonschema import exceptions, validate
from leappto.actor_support.portannotation import MsgType


class JSONClassFactory(object):
    """ Parse JSON files, generate and keep track of defined classes """
    def __init__(self, dir_path):
        logging.basicConfig()
        self.logger = logging.getLogger('JSONClassFactory')
        self.logger.setLevel(logging.DEBUG)

        # FIXME: Current idea is to use a JSON Schema to define classes
        # but we need to add 'superclass' to JSON Schema vocabulary to
        # keep track of hierarchy. Also 'properties' are being ignored
        # by now, it should be properly handled if necessity shows up
        self._schema = {
            'title': 'Class',
            'type': 'object',
            'properties': {
                'type': {'type': 'string'},
                'superclass': {'type': 'string'},
                'properties': {'type': 'object'}
            }
        }

        self._classes = {}

        if not os.path.isdir(dir_path):
            self.logger.warning("%s is not a dir", dir_path)
            return

        classes_data = []
        for json_file in os.listdir(dir_path):
            if not json_file.endswith('.json'):
                self.logger.warning("%s not JSON file ignored", json_file)
                continue
            else:
                data = self._parse_json_file(os.path.join(dir_path, json_file))
                if data:
                    classes_data.append((data, json_file))

        self._generate_all_classes(classes_data)

    @property
    def classes(self):
        """ Return a list of all generated classes """
        return self._classes.keys()

    def _parse_json_file(self, file_path):
        """ Parse and validate JSON file """
        with open(file_path, 'r') as stream:
            try:
                class_data = json.load(stream)
            except ValueError:
                self.logger.warning("%s: decoding JSON has failed", file_path)
                return None

            try:
                validate(class_data, self._schema)
            except exceptions.ValidationError as err:
                self.logger.warning("%s: validating JSON has failed: %s",
                                    file_path, err)
                return None

            return class_data

    def _generate_class(self, data, name):
        """ Generate Class from data """

        superclass_name = None
        if u'superclass' in data:
            superclass_name = data[u'superclass'].encode('ascii')

        if superclass_name:
            superclass = self.get_class(superclass_name)
            if superclass:
                self._classes.update({name: type(name, (superclass,), {})})
                return

        self._classes.update({name: type(name, (MsgType,), {})})

    def _generate_all_classes(self, classes_data):
        """ Generate all classes """
        while True:
            pending = []
            something_built = False

            for data, name in classes_data:
                if name in self.classes:
                    continue

                if u'superclass' not in data:
                    self._generate_class(data)
                    something_built = True
                    continue

                if data[u'superclass'].encode('ascii') in self.classes:
                    self._generate_class(data)
                    something_built = True
                    continue

                pending.append(name)

            if not pending:
                break
            elif not something_built:
                self.logger.warning("Classes not built for missing deps: %s",
                                    pending)

                break

    def get_class(self, name):
        """ Return generated class by name """
        if name not in self._classes.keys():
            return None

        return self._classes[name]
