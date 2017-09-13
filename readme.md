# IP Reporter

## IP Reporter 是什么？

IP Reporter 是一款监测电脑上 IP 地址变动的小工具，一旦电脑的 IP 地址发生变化，能够向指定的邮箱发送通知邮件。

然而这有什么用呢？请继续阅读~

## 使用场景

我开发这款小工具的初衷是用于 **远程桌面连接**。

我办公室有台电脑，家里也有台电脑，经常需要从家里远程连接办公室的电脑。如何连接呢？很简单，只要获得办公室电脑的 IP 地址就行了（假设是 `114.119.120.100`）。我办公室的网络配置比较特殊，没有配备路由器，电脑经由公用的大型交换机直接暴露在外网中，也就是说可以从外部直接访问到 `114.119.120.100` 这个 IP 地址。

于是，我在家里的电脑上打开远程桌面连接，输入办公室电脑的 IP 地址，连接成功了！到此为止一切正常。

然而问题来了，我办公室的电脑并不能保持 `114.119.120.100` 这个 IP 地址不变，由于租约到期、电脑重启、停电导致的网络设备重启等原因，这个 IP 地址经常在网段内波动，比如变成 `114.119.120.150` 等，如此以来，远程桌面就时常连接不上了。

针对这个问题，最简单的解决办法是：请求上级路由器的管理员给我分配一个静态 IP 地址，这样就能一劳永逸了。然而我并没有这个权限，也找不到这个管理员~

索性我就写了这个小工具，让它长期运行在办公室的电脑上，一旦 IP 地址发生变化，就向我发送邮件汇报。如此以来，不管 IP 地址如何变化，我总能在家中得知新的 IP 地址，然后重新配置远程桌面连接，一切又畅通了~

## 使用方法

### 环境配置

1. 安装 Python 环境(Python3.5.2 测试通过)

2. 将 python 目录和 python/Scripts 目录加入**系统环境变量** `PATH` 中（加入用户环境变量不行！）

3. 安装 Python 的第三方库 `pypiwin32`，命令为 `pip install pypiwin32`

4. 将 `python\Lib\site-packages\win32` 和 `python\Lib\site-packages\pywin32_system32` 目录也加入**系统环境变量** `PATH` 中。参见：[Can't start Windows service written in Python (win32serviceutil)](https://stackoverflow.com/questions/8943371/cant-start-windows-service-written-in-python-win32serviceutil)

5. 设置发件箱和收件箱：在**系统环境变量**中添加条目 `ipreporter`（注意：不是在 `PATH` 变量内，而是与其并列），其值为 `发件箱,发件箱SMTP服务器,发件箱密码,收件箱1,收件箱2,...`，如：`officePC@163.com,smtp.163.com,654321,Tom@163.com,Tom@qq.com`

> **注意：所使用的发件箱必须先开通 SMTP 服务！**
> 
> 主流的邮件服务商如：163、新浪、qq 等均默认**不开通** SMTP 服务！

### 使用 

有 2 种使用方式，一是脚本方式 `ip_reporter.py`、二是注册为 Windows 服务 `ip_reporter_service.py`。详情如下：

#### 1. 脚本方式

直接执行 `ip_reporter.py` 脚本（双击或在 cmd 中打开均可）即可。

优点是非常简单，缺点也很明显：机器一旦重启就 gg 了，除非你把它设为开机自动启动。然而开机自动启动也有缺陷：一是设置麻烦，需要借助第三方工具；二是脚本启动时很可能一些关键模块还没加载完成，导致脚本启动失败。

因此我们需要更好的方式来让脚本保持后台运行，且能够开机自启。放眼望去，Windows 服务绝对是最合适的方法了~

但我依然保留脚本方式，这样测试程序 bug 时很方便~

#### 2. 安装为 Windows 服务

1. 以管理员身份打开 cmd，并进入项目目录

2. 输入命令 `py ip_reporter_service.py install` 安装服务

3. 打开服务管理器，已经能看到 `IP Reporter Service` 这项服务了
    
    服务管理器的打开方法：按下 `<Win>+<R>` 组合键，然后输入 `services.msc`
    
    ![服务安装成功](http://os09d5k4j.bkt.clouddn.com/image/170913/0iij34eiLJ.png?imageslim)

4. 在该服务的属性中将其设为 `自动` 或 `自动（延迟启动）` 即可
    ![mark](http://os09d5k4j.bkt.clouddn.com/image/170913/7BJKg444KA.png?imageslim)

5. 当然，你也可以在 cmd 中完成 2、3、4 步的操作：`py ip_reporter_service.py --startup auto install`

6. 启动服务。可以在服务管理器中点击“启动”，也可以使用命令行：`py ip_reporter_service.py start`

7. 享受 python 脚本带来的自动化快感吧~

> 如果要卸载该服务，请使用命令：`py ip_reporter_service.py remove`

## 错误排查

由于 IP Reporter 并没有在各种环境下进行充分测试，所以不排除发生错误的可能。

如发生错误，请检查项目下的 `log` 目录，其中有 3 个日志文件：

- `reporter.log`：脚本方式运行时的日志记录
- `service.log`：Windows 服务方式运行时的日志记录
- `email.log`：两种运行方式下发送的邮件记录

使用愉快~
