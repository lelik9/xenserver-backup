from app import mongo
from bson import ObjectId


class HostsModel:
    """
        Host model:
            {
            "master" : Pool master IP: str,
            "hosts" : [
                        {
                            "obj" : xen host object: str,
                            "name" : host name: str,
                            "mem_free" : host free memory: int,
                            "ip" : host IP address: str,
                            "metrics" : xen metrics object: str,
                            "live" : host state: boolean,
                            "mem_total" : total host memory: int
                        },
                    ],
            "login" : login of pool master host: str,
            "password" : password of pool master host: str,
            "pool" : pool name: str,
            "vm" : [
                        {
                            "obj" : xen VM object: str,
                            "name" : VM name,
                            "metrics" : xen metrics object: str,
                            "state" : VM state: list,
                            "memory" : memory of VM: int,
                            "CPU" : number of VM CPU: int
                        },
                    ],
            "sr" : [
                        {
                            "obj" : xen SR object: str,
                            "name" : SR name,
                            "utilization" : Used space on disk: int,
                            "shared" : is SR shared: boolean,
                            "type" : SR type: str,
                            "size" : total SR size: int
                        },
                    ]
            }

    """
    instance = None
    db = None

    def __init__(self, default=False):
        if not default:
            raise SyntaxError("For creating class object use 'get_instance' method")
        else:
            HostsModel.instance = self

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            HostsModel(default=True)
        return cls.instance

    @classmethod
    def set_db(cls, db):
        cls.db = db

    def add_host(self, args):
        self.db.insert(args)

    def get_hosts(self):
        nodes = []

        for node in self.db.find({}, {'_id': 0, 'vm': 0, 'sr': 0, 'login': 0,
                                             'password': 0}):
            nodes.append(node)

        return nodes

    def get_vm(self):
        vm = []

        for node in self.db.find({}, {'_id': 0, 'hosts': 0, 'sr': 0, 'login': 0,
                                             'password': 0}):
            vm.append(node)

        return vm

    def get_sr(self):
        sr = []

        for node in self.db.find({}, {'_id': 0, 'hosts': 0, 'vm': 0, 'login': 0,
                                             'password': 0}):
            sr.append(node)

        return sr

    def get_pool_of_vm(self, vm_obj):
        host = self.db.find_one({'vm.obj': vm_obj})

        return host

    def get_pool_of_host(self, host_obj):
        host = self.db.find_one({'hosts.obj': host_obj})

        return host

    def set_host_info(self, host_ip, key, info):
        return self.db.update({'master': host_ip}, {'$set': {key: info}})

    def get_pool(self, pool_name):
        return self.db.find_one({'pool': pool_name})

    def rm_pool(self, host):
        return self.db.remove({'hosts.obj': host})


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
    """
        Backup meta model:
            {
                '_id': backup time: str,
                'vm_name': VM name: str,
                'vdis': [{
                    'name_label': ,
                    'virtual_size': ,
                    'type': ,
                    'sharable': ,
                    'read_only': ,
                    'other_config': ,
                    'tags': ,
                    'managed': ,
                    'missing': ,
                    'vbd_meta': [{
                        'device': ,
                        'userdevice': ,
                        'bootable': ,
                        'mode': ,
                        'type': ,
                        'empty': ,
                        'unpluggable': ,
                        'other_config': ,
                        'qos_algorithm_type': ,
                        'qos_algorithm_params':
                    }],
                    'backup_file': vdi backup file name
                }],
                'vm': {
                    'memory_dynamic_min': ,
                    'memory_dynamic_max': ,
                    'memory_static_max': ,
                    'memory_static_min': ,
                    'actions_after_shutdown': ,
                    'actions_after_crash': ,
                    'actions_after_reboot': ,
                    'HVM_boot_policy': ,
                    'HVM_boot_params': ,
                    'HVM_shadow_multiplier': ,
                    'VCPUs_at_startup': ,
                    'VCPUs_max': ,
                    'other_config':
                },
                'vifs': {
                    'device': ,
                    'MTU': ,
                    'MAC': ,
                    'other_config': ,
                    'name':
                },
                'meta_file': backup meta file name: str,
                'backup_sr': storage when store backup: str
            }
    """
    @staticmethod
    def add_backup_info(obj):
        mongo.db.backup.insert(obj)

    @staticmethod
    def get_backup(id):
        return mongo.db.backup.find_one({'_id': id})

    @staticmethod
    def remove_backup(id):
        mongo.db.backup.remove({'_id': ObjectId(id)})

    @staticmethod
    def get_backups():
        backups = list(mongo.db.backup.find({}, {'vm_name': 1}))

        return backups


class BackupStorageModel:
    """
        Backup storage model:
            {
            '_id': name of backup_restore storage,
            'share_path': share name,
            'sr_type': share type (smb, nfs, folder),
            'login': login for smb share,
            'password': password for smb share,
        }
    """
    @staticmethod
    def add_storage(obj):
        mongo.db.backup_sr.insert(obj)

    @staticmethod
    def get_backup_sr_wo_login():
        srs = []

        for sr in mongo.db.backup_sr.find({}, {'login': 0, 'password': 0}):
            srs.append(sr)

        return srs

    @staticmethod
    def get_backup_sr(sr_name):
        return mongo.db.backup_sr.find_one({'_id': sr_name})

# class StorageModel:
#
#     @staticmethod
#     def add_storage(obj):
#         mongo.db.sr.insert(obj)
#
#     @staticmethod
#     def get_backup_sr_paths():
#         paths = []
#
#         for path in mongo.db.sr.find({}, {'share_path': 1}):
#             paths.append(path)
#
#         return paths
