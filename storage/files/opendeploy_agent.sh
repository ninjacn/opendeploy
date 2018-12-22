#!/bin/bash
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

# 全量模式
release_by_fullmode() {
    release_path=$1
    release_num=$2
    rm -f ${release_path}
    if [ "$?" -ne 0 ]
    then
        echo "清理软链出错, 请手动删除${release_path}"
        exit 1
    fi

    release_version_path=${release_path}_${release_num} 
    if [ -e ${release_version_path} ]
    then
        ln -s ${release_version_path} ${release_path}
    fi
}

rollback_by_fullmode() {
    rollback_path=$1
    rollback_num=$2
    rm -f ${rollback_path}
    if [ "$?" -ne 0 ]
    then
        echo "清理软链出错, 请手动删除${rollback_path}"
        exit 1
    fi

    rollback_version_path=${rollback_path}_${release_num} 
    if [ -e ${rollback_version_path} ]
    then
        ln -s ${rollback_version_path} ${rollback_path}
    fi
}

#release_by_fullmode /Users/yaopengming/Code/test/abc 1
rollback_by_fullmode /Users/yaopengming/Code/test/abc 1

