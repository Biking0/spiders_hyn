# 配置环境
## 安装virtualenv
```
pip install virtualenv
```
## 创建虚拟环境
如果python2与python3并存:
```
virtualenv -p /usr/bin/python2.7 py2[环境名]
```
没有python3:
```
virtualenv py2[环境名]
```
## 启动虚拟环境
```
source py2/bin/activate
```
## 安装包
```
pip install -r requirements.txt
```
如果scrapy安装失败，就再安装一下python-dev
```
sudo apt-get install python-dev
```
# 启动(lin上的第一个flybe 爬虫,数字不写的话默认为1)
```
python ww_spider.py lin 1
```

##  2018/12/10 14:22 
## doc 该目录下为各个爬虫帮助文档 

## test 2019/03/18