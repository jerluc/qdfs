import os
import os.path
import shutil
import tempfile

# TODO: Cross-platform behavior here is likely sketchy
DEFAULT_ROOT_DIR = '/tmp/qdfs'

def create_temp_dir(root_dir):
    try:
        os.makedirs(root_dir)
    except:
        # Presumably, this will explode if the file already exists. But even if it blew up for
        # some other reason, trying to create a new temp directory in that location will still blow
        # up below, so ignoring this exception is probably safe

        # TODO: How to make this suck less
        pass
    return tempfile.mkdtemp(prefix='dn-', dir=DEFAULT_ROOT_DIR)

class StorageError(Exception):
    # TODO: Add some more structured fields here for exception handling purposes
    pass

class LocalFileStore(object):
    '''
    A file store implementation for working against the local filesystem. This is mostly used
    internally for data nodes to interact with their underlying "native" storage, but considering
    that this implementation may also be useful for minimal setups or for testing purposes, it will
    remain exported, for now.

    root_dir is the root directory under which all paths are relativized.
    '''
    def __init__(self, root_dir=DEFAULT_ROOT_DIR):
        self.root_dir = create_temp_dir(root_dir)

    def _rooted(self, path):
        path = path.lstrip(os.path.sep)
        return os.path.join(self.root_dir, path)

    def info(self):
        statvfs = os.statvfs(self.root_dir)
        return {
            'root': self.root_dir,
            'total': statvfs.f_frsize * statvfs.f_blocks,
            'free': statvfs.f_frsize * statvfs.f_bfree,
            'available': statvfs.f_frsize * statvfs.f_bavail
        }

    def stat(self, path):
        full_path = self._rooted(path)
        stat = os.stat(full_path)
        return {
            'ctime': stat.st_ctime,
            'atime': stat.st_atime,
            'mtime': stat.st_mtime,
            'mode': stat.st_mode,
            'uid': stat.st_uid,
            'gid': stat.st_gid,
            'size': stat.st_size
        }

    def open(self, path, mode=None):
        mode = mode if mode else 'r'
        self._ensure_exists(path)
        full_path = self._rooted(path)
        return open(full_path, mode)

    def append(self, path):
        return self.open(path, 'a')
    
    def write(self, path, data, offset=0):
        with self.open(path, 'w') as f:
            f.seek(offset)
            f.write(data)

    def read(self, path, offset=0, num_bytes=-1):
        data = None
        with self.open(path) as f:
            f.seek(offset)
            data = f.read(num_bytes)
        return data

    def list(self, path):
        self._ensure_exists(path)
        if self.is_file(path):
            raise StorageError('Cannot list regular file: \'%s\'' % path)

        full_path = self._rooted(path)
        files = os.listdir(full_path)

        return map(lambda f: os.path.join(path, f), files)

    def _ensure_exists(self, path):
        exists = self.exists(path)
        if not exists:
            raise StorageError('No such file or directory: \'%s\'' % path) 

    def exists(self, path):
        full_path = self._rooted(path)
        return os.path.exists(full_path)

    def create_file(self, path, allow_overwrite=True):
        if self.exists(path) and not allow_overwrite:
            raise StorageError('The file [%s] already exists' % path)
       
        if not self.exists(os.path.dirname(path)):
            self.create_dir(os.path.dirname(path))

        full_path = self._rooted(path)
        with open(full_path, 'a'):
            os.utime(full_path, None)

    def create_dir(self, path, allow_overwrite=True):
        if self.exists(path) and not allow_overwrite:
            raise StorageError('The file [%s] already exists' % path)
        
        full_path = self._rooted(path)
        os.makedirs(full_path)

    def is_file(self, path):
        full_path = self._rooted(path)
        return os.path.isfile(full_path)

    def is_dir(self, path):
        full_path = self._rooted(path)
        return os.path.isdir(full_path)

    def delete(self, path, recursive=False):
        self._ensure_exists(path)
        full_path = self._rooted(path)
        if self.is_dir(path):
            if not recursive:
                raise StorageError('Refusing to delete directory \'%s\'. Did you mean to use' +
                        'recursive delete?' % path)
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)

