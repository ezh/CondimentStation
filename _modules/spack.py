# -*- coding: utf-8 -*-
'''
SPACK package manager
'''
from __future__ import absolute_import

# Import python libs
import copy
import logging

# Import salt libs
import salt.utils
from salt.exceptions import CommandExecutionError, MinionError

log = logging.getLogger(__name__)


def spack_directory():
    """ Specialized to avoid infinite recurrence """
    from os.path import join
    default = join(__grains__['userhome'], 'spack')
    return __salt__['pillar.get']('spack:directory', default)


def defaults(key=None, value=None):
    """ Default pillar values """
    from os.path import join
    try:
        _init_spack()
        from spack.cmd import default_list_scope as dls
        from spack.repository import canonicalize_path
    except ImportError:
        dls = "spack"

        def canonicalize_path(x):
            from os.path import expanduser, expandvars, abspath
            return abspath(expanduser(expandvars(x)))

    if key is not None and value is not None:
        return value
    home = __grains__['userhome']
    config_dir = join(home, '.spack')
    repo_prefix = join(home, '.spack_repos')
    values = {
        'directory': spack_directory(),
        'config_dir':
            __salt__['pillar.get']('spack:config_location', config_dir),
        'repo_prefix':
            __salt__['pillar.get']('spack:repo_prefix', repo_prefix),
        'scope':
            __salt__['pillar.get']('spack:default_config_location', dls)
    }
    values['config_dir'] = canonicalize_path(values['config_dir'])
    values['repo_prefix'] = canonicalize_path(values['repo_prefix'])
    return values[key] if key is not None else values


def module_name(name, compiler=None):
    """ Figures out module name(s) from specs """
    _init_spack()
    from spack.modules import module_types
    from spack import installed_db
    mt = module_types['tcl']

    if compiler is not None:
        names = name.split()
        names.insert(1, "%" + compiler.rstrip().lstrip())
        name = ' '.join(names)

    specs = parse_specs(name, concretize=True, normalize=True)
    result = []
    for spec in specs:
        mods = installed_db.query(spec)
        if len(mods) == 0:
            raise ValueError("No module found for %s." % spec)
        elif len(mods) > 1:
            raise ValueError(
                "More than one module matches %s (%s)." % (spec, mods))
        result.append(mt(mods[0]).use_name)
    return result


def _init_spack():
    from os.path import join, expanduser
    from os import getcwd
    from sys import path
    spackdir = spack_directory()
    libdir = join(spackdir, 'lib', 'spack')
    if libdir not in path:
        path.append(libdir)
        path.append(join(libdir, 'external'))

    import spack
    spack.debug = False
    spack.spack_working_dir = spack_directory()


def repo_exists(path, scope=None, prefix=None):
    """ Checks whether input is a known repo """
    _init_spack()
    from spack.repository import Repo
    from spack.config import get_config
    from os.path import join

    cannon = repo_path(path)
    repos = get_config('repos', defaults('scope', scope))

    repo = Repo(cannon)
    return repo.root in repos or path in repos


def repo_path(path="", prefix=None):
    _init_spack()
    from os.path import join
    from spack.repository import canonicalize_path

    if len(path) == 0:
        path = defaults('repo_prefix', prefix)
    elif path[0] not in ['/', '$', '~']:
        path = join(defaults('repo_prefix', prefix), path)
    return canonicalize_path(path)


def add_repo(path, prefix=None, scope=None):
    """ Adds path to spack repos """
    _init_spack()

    from collections import namedtuple
    from spack.repository import Repo
    from spack.config import get_config, update_config
    from spack.cmd import default_list_scope

    cannon = repo_path(path, prefix)
    repos = get_config('repos', defaults('scope', scope))
    if not repos:
        repos = []

    repo = Repo(cannon)

    if repo.root in repos or path in repos:
        return False

    repos.insert(0, cannon)
    update_config('repos', repos, defaults('scope', scope))
    return True


def parse_specs(specs, concretize=False, normalize=False):
    """ Converts spec to module name """
    _init_spack()
    from spack.cmd import parse_specs
    return parse_specs(specs, concretize=concretize, normalize=normalize)


def package_prefix(specs):
    """ Return package prefix """
    _init_spack()
    from spack.cmd import parse_specs
    packages = parse_specs(specs, concretize=True)
    if len(packages) == 0:
        raise RuntimeError("No package found")
    elif len(packages) > 1:
        raise RuntimeError("Specs correspond to more than one package")
    return packages[0].prefix


def is_installed(name, compiler=None):
    _init_spack()
    from spack import repo
    from spack.cmd import parse_specs
    names = [name] if isinstance(name, str) else name
    for name in names:
        if compiler is not None:
            name = name.split()
            name.insert(1, "%" + compiler.rstrip().lstrip())
            name = ' '.join(name)
        specs = parse_specs(name, concretize=True)
        for spec in specs:
           a = repo.get(spec)
           if not a.installed:
               return False
    return True


def install(name, keep_prefix=False, keep_stage=False, ignore_deps=False, environs=None, compiler=None):
    _init_spack()
    from spack import repo, installed_db
    from spack.cmd import parse_specs
    from os import environ
    if not isinstance(name, str):
        results = [], []
        for pkg in name:
            a, b = install(pkg, keep_prefix=keep_prefix, keep_stage=keep_stage,
                           ignore_deps=ignore_deps, environs=environs,
                           compiler=compiler)
            results[0].extend(a)
            results[1].extend(b)
        return results
    if environs is not None:
        environ.update(environs)
    if compiler is not None:
        names = name.split()
        names.insert(1, "%" + compiler.rstrip().lstrip())
        name = ' '.join(names)
    specs = parse_specs(name, concretize=True)
    packages = [repo.get(spec) for spec in specs]
    new_pkgs = [u for u in packages if not u.installed]
    for package in new_pkgs:
        with installed_db.write_transaction():
            package.do_install(
                keep_prefix=keep_prefix,
                keep_stage=keep_stage,
                ignore_deps=ignore_deps
            )
    return [p.name for p in new_pkgs if p.installed], \
        [p.name for p in new_pkgs if not p.installed]
