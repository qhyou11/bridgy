import re
import abc
import warnings
import collections
from functools import partial

from bridgy.error import MissingBastionHost

with warnings.catch_warnings():
    # Thiw warns about using the slow implementation of SequenceMatcher
    # instead of the python-Levenshtein module, which requires compilation.
    # I'd prefer for users tp simply use this tool without the need to
    # compile since the search space is probably fairly small
    warnings.filterwarnings("ignore", category=UserWarning)
    from fuzzywuzzy import fuzz

class InstanceType:
    ALL = 'ALL'
    VM = 'VM'
    ECS = 'ECS'

Bastion = collections.namedtuple("Bastion", "destination options")
Instance = collections.namedtuple("Instance", "name address aliases source container_id type username instname")
# allow there to be optional kwargs that default to None
Instance.__new__.__defaults__ = (None,) * len(Instance._fields)

class InventorySource(object):
    __metaclass__ = abc.ABCMeta

    name = "Invalid"
    bastion = None
    ssh_user = None
    ssh_options = None
    include_pattern = None
    exclude_pattern = None

    def __init__(self, *args, **kwargs):
        if 'name' in kwargs:
            self.name = "%s (%s)" % (kwargs['name'], self.name)
            self.source = kwargs['name']

        if 'bastion' in kwargs:
            if 'address' not in kwargs['bastion']:
                raise MissingBastionHost

            if 'user' in kwargs['bastion']:
                destination = '{user}@{host}'.format(user=kwargs['bastion']['user'],
                                                     host=kwargs['bastion']['address'])
            else:
                destination = kwargs['bastion']['address']

            bastion_options = ''
            if 'options' in kwargs['bastion']:
                bastion_options = kwargs['bastion']['options']

            self.bastion = Bastion(destination=destination, options=bastion_options)

        if 'ssh' in kwargs:
            if 'user' in kwargs['ssh']:
                self.ssh_user = kwargs['ssh']['user']

            if 'options' in kwargs['ssh']:
                self.ssh_options = kwargs['ssh']['options']
            else:
                self.ssh_options = ''
        
        if 'include_pattern' in kwargs:
            self.include_pattern = kwargs['include_pattern']
        if 'exclude_pattern' in kwargs:
            self.exclude_pattern = kwargs['exclude_pattern']

    def instance_filter(self, instance, include_re=None, exclude_re=None):
        comparables = [instance.name, instance.address]

        if instance.aliases:
            comparables.extend(list(instance.aliases))

        if include_re:
            for name in comparables:
                if include_re.search(name):
                    return True
            return False
        elif exclude_re:
            for name in comparables:
                if exclude_re.search(name):
                    return False
            return True
        else:
            return True

    def filter(self, all_instances):
        include_re, exclude_re = None, None
        if self.include_pattern:
            include_re = re.compile(self.include_pattern)
        if self.exclude_pattern:
            exclude_re = re.compile(self.exclude_pattern)

        config_instance_filter = partial(self.instance_filter, include_re=include_re, exclude_re=exclude_re)
        return list(filter(config_instance_filter, all_instances))

    @abc.abstractmethod
    def update(self): pass

    @abc.abstractmethod
    def instances(self, stub=True): pass

    def search(self, targets, partial=True, fuzzy=False):
        allInstances = self.instances()
        matchedInstances = set()

        for host in targets:
            for instance in allInstances:
                names = [instance.name]
                if instance.aliases != None:
                    names += list(instance.aliases)
                for name in names:
                    if host.lower() == name.lower():
                        matchedInstances.add((100, instance))
                    elif partial and host.lower() in name.lower():
                        matchedInstances.add((99, instance))

                    if fuzzy:
                        score = fuzz.partial_ratio(host.lower(), name.lower())
                        if score > 85 or host.lower() in name.lower():
                            matchedInstances.add((score, instance))

        # it is possible for the same instance to be matched, if so, it should only
        # appear on the return list once (still ordered by the most probable match)
        return list(collections.OrderedDict([(v, None) for k, v in sorted(list(matchedInstances))]).keys())


class InventorySet(InventorySource):

    def __init__(self, inventories=None, **kwargs):
        super(InventorySet, self).__init__(inventories, **kwargs)
        self.inventories = []

        if inventories != None:
            if not isinstance(inventories, list) and not isinstance(inventories, tuple):
                raise RuntimeError("InventorySet only takes a list of inventories. Given: %s" % repr(type(inventories)))

            for inventory in inventories:
                self.add(inventory)

    def add(self, inventory):
        if not isinstance(inventory, InventorySource):
            raise RuntimeError("InventorySet item is not an inventory. Given: %s" % repr(type(inventory)))

        self.inventories.append(inventory)

    @property
    def name(self):
        return " + ".join([inventory.name for inventory in self.inventories])

    def update(self, filter_sources=tuple()):
        for inventory in self.inventories:
            if len(filter_sources) == 0 or (len(filter_sources) > 0 and inventory.source in filter_sources):
                inventory.update()

    def instances(self, stub=True, filter_sources=tuple()):
        instances = []

        for inventory in self.inventories:
            if len(filter_sources) == 0 or (len(filter_sources) > 0 and inventory.source in filter_sources):
                instances.extend(inventory.instances())

        return instances

    def search(self, targets, partial=True, fuzzy=False, filter_sources=tuple()):
        instances = []

        for inventory in self.inventories:
            if len(filter_sources) == 0 or (len(filter_sources) > 0 and inventory.source in filter_sources):
                instances.extend(inventory.search(targets, partial, fuzzy))

        return instances