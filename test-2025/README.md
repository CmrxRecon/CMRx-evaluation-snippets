# test phase 流程

- 从excel下载表格，获取test信息，解析为json对象
- 读取记录运行记录的文件（队名、时间、测试状态），拉取新发现的镜像
- 创建容器
- 检查结果并打分
- 发送邮件通知参赛者

## 容器规范

- 代码目录 /app
- 输入目录 /input
- 输出目录 /output

Dockerfile示例
``` Dockerfile
## Start from this Docker image
## for the version, we recommend the version xx.xx less than 22.02
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-devel

## Set workdir in Docker Container
# set default workdir in your docker container
# In other words your scripts will run from this directory
WORKDIR /app

## Copy all your files of the current folder into Docker Container
COPY ./ /app

## Install requirements
RUN pip3 install -r requirements.txt

## Make Docker container executable
ENTRYPOINT ["/opt/conda/bin/python", "inference.py"]
```

## status.json

status: infered, tested, notified

## 打分程序

- 根据GT找输出文件，如果缺少输出文件则进行提示
- shape mismatch的图像，需要输出二者shape来提示
