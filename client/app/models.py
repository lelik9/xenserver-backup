# coding=utf-8
from bson import ObjectId
from functools import wraps


def singletone(cls):
    instance = None

    @wraps(cls)
    def wrapper(*args, **kwargs):
        if instance is None:
            singletone.instance = cls(*args, **kwargs)
        return singletone.instance
    return wrapper


@singletone
class BaseModel(object):
    instance = None
    db = None

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls(default=True)
        return cls.instance

    @classmethod
    def set_db(cls, db):
        cls.db = db


class HostsModel(BaseModel):
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

    def __init__(self, default=False):
        if not default:
            raise SyntaxError("For creating class object use 'get_instance' method")
        else:
            HostsModel.instance = self

    def add_host(self, args):
        self.db.insert(args)

    def get_hosts(self):
        nodes = []

        for node in self.db.find({}, {'_id': 0, 'vm': 0, 'sr': 0, 'login': 0, 'password': 0}):
            nodes.append(node)

        return nodes

    def get_vm(self):
        vm = []

        for node in self.db.find({}, {'_id': 0, 'hosts': 0, 'sr': 0, 'login': 0, 'password': 0}):
            vm.append(node)

        return vm

    def get_sr(self, pool):
        return self.db.find_one({"pool": pool}, {'_id': 0, 'hosts': 0, 'vm': 0, 'login': 0,
                                                 'password': 0})

    def get_pool_of_vm(self, vm_obj):
        host = self.db.find_one({'vm.obj': vm_obj})

        return host

    def get_pool_by_name(self, pool_name):
        host = self.db.find_one({'pool': pool_name})

        return host

    def set_host_info(self, host_ip, key, info):
        return self.db.update({'master': host_ip}, {'$set': {key: info}})

    def get_pool(self, pool_name):
        return self.db.find_one({'pool': pool_name})

    def rm_pool(self, host):
        return self.db.remove({'hosts.obj': host})


class VmModel(BaseModel):
    def __init__(self, default=False):
        if not default:
            raise SyntaxError("For creating class object use 'get_instance' method")
        else:
            BackupModel.instance = self

    def add_vms(self, **kwargs):
        self.db.insert(kwargs)

    def get_vms(self, host_id):
        if host_id == 'all':
            vms = self.db.find()
        else:
            vms = self.db.find({'host_id': host_id})

        all_vm = list(vms)

        return all_vm

    def get_vm(self, vm_id):
        vm = self.db.find_one({'_id': ObjectId(vm_id)})

        return vm


class BackupModel(BaseModel):
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

    def __init__(self, default=False):
        if not default:
            raise SyntaxError("For creating class object use 'get_instance' method")
        else:
            BackupModel.instance = self

    def add_backup_info(self, obj):
        self.db.insert(obj)

    def get_backup(self, id):
        return self.db.find_one({'_id': id})

    def remove_backup(self, id):
        self.db.remove({'_id': ObjectId(id)})

    def get_backups(self):
        backups = list(self.db.find({}, {'vm_name': 1}))

        return backups


class BackupStorageModel(BaseModel):
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

    # def __init__(self, default=False):
    #     if not default:
    #         raise SyntaxError("For creating class object use 'get_instance' method")
    #     else:
    #         BackupStorageModel.instance = self

    def add_storage(self, obj):
        self.db.insert(obj)

    def get_backup_sr_wo_login(self):
        srs = []

        for sr in self.db.find({}, {'login': 0, 'password': 0}):
            srs.append(sr)

        return srs

    def get_backup_sr(self, sr_name):
        return self.db.find_one({'_id': sr_name})
