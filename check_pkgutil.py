import pkgutil
print('pkgutil.__file__ =', pkgutil.__file__)
print('has get_loader =', hasattr(pkgutil, 'get_loader'))
print('get_loader =', getattr(pkgutil, 'get_loader', None))
