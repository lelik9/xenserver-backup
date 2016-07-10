from __future__ import print_function
from app import mongo
from bson import ObjectId


class HostsModel:
    def __init__(self):
        pass

    @staticmethod
    def add_host(args):
        id = mongo.db.hosts.insert(args)

        return str(id)

    @staticmethod
    def get_hosts():
        nodes = []

        for node in mongo.db.hosts.find({}, {'_id': 0, 'vm': 0, 'sr': 0, 'login': 0,
                                             'password': 0}):
            nodes.append(node)

        return nodes

    @staticmethod
    def get_vm():
        vm = []

        for node in mongo.db.hosts.find({}, {'_id': 0, 'hosts': 0, 'sr': 0, 'login': 0,
                                             'password': 0}):
            vm.append(node)

        return vm

    @staticmethod
    def get_sr():
        sr = []

        for node in mongo.db.hosts.find({}, {'_id': 0, 'hosts': 0, 'vm': 0, 'login': 0,
                                             'password': 0}):
            sr.append(node)

        return sr

    # @staticmethod
    # def get_host(id):
    #     host = mongo.db.hosts.find_one({'_id': ObjectId(id)})
    #
    #     return host

    @staticmethod
    def set_host_info(host_ip, key, info):
        return mongo.db.hosts.update({'master': host_ip}, {'$set': {key: info}})

    @staticmethod
    def get_pool(pool_name):
        return mongo.db.hosts.find_one({'pool': pool_name})

    @staticmethod
    def rm_pool(host):
        return mongo.db.hosts.remove({'hosts.obj': host})


class VmModel:
    @staticmethod
    def add_vms(**kwargs):
        mongo.db.vm.insert(kwargs)

    @staticmethod
    def get_vms(host_id):
        if host_id == 'all':
            vms = mongo.db.vm.find()
        else:
            vms = mongo.db.vm.find({'host_id': host_id})

        all_vm = list(vms)

        return all_vm

    @staticmethod
    def get_vm(vm_id):
        vm = mongo.db.vm.find_one({'_id': ObjectId(vm_id)})

        return vm


class BackupModel:
    @staticmethod
    def add_backup_info(**kwargs):
        mongo.db.backup.insert(kwargs)

    @staticmethod
    def get_vms_backups(id):
        if id == 'all':
            backups = mongo.db.backup.find()
        else:
            backups = mongo.db.backup.find({'vm_id': id})

        all_backup = list(backups)
        print(all_backup)
        return all_backup

    @staticmethod
    def remove_backup(id):
        mongo.db.backup.remove({'_id': ObjectId(id)})

    @staticmethod
    def get_backup_info(id):
        backup = mongo.db.backup.find({'_id': ObjectId(id)}, {'vdis': 1})

        return backup


class BackupStorageModel:
    @staticmethod
    def add_storage(**kwargs):
        mongo.db.backup_sr.insert(kwargs)


class StorageModel:
    @staticmethod
    def add_storage(**kwargs):
        res = mongo.db.sr.find_one({'sr_obj': kwargs['sr_obj']})
        print(res)
