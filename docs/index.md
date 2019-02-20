## 概述

Opendeploy是简单、易用的代码部署系统。该系统使用Python语言结合Django框架编写，依赖于git、rsync等系统组件。系统安装部署基于Docker完成，所以整个安装过程很简单，不需要额外关于Python、Django或其它组件版本及是否支持。

* 项目地址[https://github.com/ninjacn/opendeploy.git](https://github.com/ninjacn/opendeploy.git)

## 主要特性
* 支持增量及全量两种部署模式
* 支持多环境，每个环境关联不同的主机组及Hook
* Webhook - 支持Github及gitlab,可实现从代码提交到部署完全自动化
* 部署前Hook - 支持部署前在发布机上执行相关任务, 如PHP语言的composer，或调整环境相关配置路径等
* 部署后Hook - 支持同步到目标服务器之后运行相关任务，如清理一些缓存，重启相应服务等
* 同步文件支持排除单个文件或路径，支持删除选项(保证仓库与目标服务器数据一致, 慎重使用), 排除格式可参考rsync.<code>man rsync</code>
* 账号认证支持LDAP及本地认证
* 公有云(阿里云和腾讯云)服务器数据导入
* 消息通知 - 支持邮件及钉钉机器人

## 概念

### 部署模式
* 增量
> 增量模式为默认模式。该模式是指目标服务器路径为固定路径，所有需要部署的文件都会同步(<code>rsync</code>)到这个路径下。如果你的项目已经正常运行，该模式不会影响现有服务。项目路径下生成的文件(缓存、日志或临时文件等)都会保留。
* 全量
> 全量模式是指每次部署系统都会将所有文件部署到目标服务器，并且在目标服务器上生成的目录名为<code>项目名+发布系统ID</code>; 系统会建立一个软链接，源路径为目标服务器上真实路径，目标路径(软链)为不带发布系统ID的路径(后台配置)。nginx或其它web服务器根路径会指向这个软链接。

## 部分截图
![前台](images/frontend01.png)
![前台](images/frontend02.png)
![前台](images/frontend03.png)
![后台](images/backend01.png)
