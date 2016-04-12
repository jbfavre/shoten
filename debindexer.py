#!/usr/bin/env python
''' Copyright (c) 2013 Jean Baptiste Favre.
    Debian packages dependencies indexer.
'''

import apt_pkg
import py2neo

def get_priority(pkg_name):
    global cache
    package = cache[pkg_name]
    return getattr(package, 'priority', 'None')

def get_section(pkg_name):
    global cache
    package = cache[pkg_name]
    return package.section

def get_essential_flag(pkg_name):
    global cache
    package = cache[pkg_name]
    return getattr(package, 'essential', 'No')

def pkg_found(neo4jCypher, name, version):
    statement = "MATCH(n:package {name:{name},version:{version}}) RETURN n"
    result = neo4jCypher.execute(statement, name=name, version=version)
    return iter(result.to_subgraph().nodes).next()

def index_debian_repo():
    py2neo.authenticate("localhost:7474", "neo4j", "neo")
    neo4jGraph = py2neo.Graph('http://localhost:7474/db/data/')
    #neo4jGraph.schema.create_uniqueness_constraint('pkg', 'name')
    neo4jCypher = neo4jGraph.cypher

    apt_pkg.init_config()
    apt_pkg.init_system()
    cache = apt_pkg.Cache()
    # get list of packages:

    n = 0
    last_pkg_name=''
    for pkg in sorted(cache.packages, key=lambda pkg: pkg.name):
        new_pkg_name = pkg.name
        # create a pkg node in neo4j
        pkg_node = py2neo.Node(
            'pkg',
            name=pkg.name,
            section=pkg.section
        )
        try:
            pkg_node, = neo4jGraph.create(pkg_node)
        except:
            statement = "MATCH(n:package {name:{name}}) RETURN n"
            result = neo4jCypher.execute(statement, name=pkg.name)
            pkg_node = pkg_found(neo4jCypher, pkg.name)
            pass
        # create a pkg_version node in neo4j for each version
        # of the package and link it to pkg node
        for pkgver in pkg.version_list:
            src_node = py2neo.Node(
                'pkg_version',
                pkgid=pkg.name+'='+pkgver.ver_str,
                name=pkg.name,
                version=pkgver.ver_str,
                priority=pkg.priority,
                installed_size=pkgver.installed_size
            )
            try:
                src_node, = neo4jGraph.create(src_node)
            except:
                src_node = pkg_found(neo4jCypher, pkg.name, pkgver.ver_str)
                pass
            relation = py2neo.Relationship(pkg_node, 'exists_in_version', src_node)
            neo4jGraph.create(relation)
            for dependencies in pkgver.depends_list.get('Depends', []):
                for dependency in dependencies:
                    pkg_list = dependency.all_targets()
                    for pkgdep in pkg_list:
                        dst_node = py2neo.Node(
                            'pkg',
                            pkgid=pkgdep.parent_pkg.name+'='+pkgdep.ver_str,
                            name=pkgdep.parent_pkg.name,
                            version=pkgdep.ver_str,
                            section=pkgdep.section,
                            priority=pkgdep.priority_str,
                            installed_size=pkgdep.installed_size
                        )
                        try:
                            dst_node, = neo4jGraph.create(dst_node)
                        except:
                            dst_node = pkg_found(neo4jCypher, pkgdep.parent_pkg.name, pkgdep.ver_str)
                            pass
                        relation = py2neo.Relationship(src_node, dependency.dep_type, dst_node)
                        neo4jGraph.create(relation)
            n += 1
            if n % 1000 == 0:
                print "%d / /%d" % (n, len(cache.packages))


if __name__ == '__main__':
    index_debian_repo()
    print "Saving graph file..."
