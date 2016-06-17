#!/usr/bin/env python
''' Copyright (c) 2013 Jean Baptiste Favre.
    Debian packages dependencies indexer.
'''

import sys

import apt_pkg
import py2neo
import py2neo.ext.batman

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

def register_package(neo4jGraph, package):
    statement = "MERGE (p:Package {name:{name}})"
    print "MERGE (p:Package {name:'%s'})" % package.name
    neo4jGraph.run(statement, name=package.name)

def index_debian_repo():
    py2neo.authenticate('localhost:7474', 'neo4j', 'neo')
    neo4jGraph = py2neo.Graph(host='localhost')

    apt_pkg.init_config()
    apt_pkg.init_system()
    cache = apt_pkg.Cache()

    # Register packages
    package_nb=0
    for package in sorted(cache.packages, key=lambda package: package.name):
        if package_nb>100:
            sys.exit(0)
        package_nb=package_nb+1
        for version in package.version_list:
            statement = """
                MERGE (p:Package {name:{name}})
                MERGE (v:Version {id:{version_id}, package:{name}, version:{version}})
                MERGE (p)-[:HAS_VERSION]->(v)
            """
            neo4jGraph.run(statement, name=package.name, \
                                      version=version.ver_str, \
                                      version_id=package.name+'_'+version.ver_str \
            )
            for dependency_level in version.depends_list:
                dependency_list = version.depends_list[dependency_level]
                for depend in dependency_list:
                    for dependency in depend:
                        target_version =  'Undefined'
                        if dependency.parent_ver.ver_str != '':
                            target_version = dependency.parent_ver.ver_str
                        statement = """
                            MERGE (op:Package {name:{origin_name}})
                            MERGE (ov:Version {id:{origin_id}, package:{origin_name}, version:{origin_version}})
                            MERGE (op)-[:HAS_VERSION]->(ov)
                            MERGE (tp:Package {name:{target_name}})
                            MERGE (tv:Version {id:{target_id}, package:{target_name}, version:{target_version}})
                            MERGE (tp)-[:HAS_VERSION]->(tv)
                        """
                        statement = statement + \
                                    'MERGE (ov)-[:' + dependency_level +\
                                    ' {type:{dependency_level},origin:{origin_id}, target:{target_id}}]->(tv)'
                        neo4jGraph.run(statement, origin_id=dependency.parent_pkg.name+'_'+dependency.parent_ver.ver_str, \
                                                  origin_name=dependency.parent_pkg.name, \
                                                  origin_version=dependency.parent_ver.ver_str, \
                                                  target_id=dependency.target_pkg.name+'_'+target_version, \
                                                  target_name=dependency.target_pkg.name, \
                                                  target_version=target_version, \
                                                  dependency_level=dependency_level \
                        )

if __name__ == '__main__':
    index_debian_repo()
    print "Saving graph file..."