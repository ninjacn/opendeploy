## Hook - 钩子

目前支持两个钩子，发布前钩子和发布后钩子。

### 发布前钩子(在发布机执行)

* 可以是任意脚本语言，只要发布机支持。比如bash shell, php,python等
* 当前工作目录为工作区路径(可以理解为项目根路径)

比如: 发布前设置该环境为生产, 将生产环境配置文件链接到配置文件路径:
```
#!/bin/bash

cp -f ./web/index_production.php ./web/index.php
```


### 发布后钩子(在目标机器执行)

* 可以是任意脚本语言，只要目标机器支持。比如bash shell, php,python等
* 当前工作目录为目标机器部署路径

比如: 清理目标机器opcache(PHP缓存):
```
#!/bin/bash

curl -s http://127.0.0.1/opcache.php
php -r "opcache_reset() ? exit(0) : exit(1);"
```
