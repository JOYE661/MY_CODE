镜像地址

https://b3h3z45r.mirror.aliyuncs.com

## 部署前提条件

1. **Docker已安装并运行**：确保本地Docker Desktop（macOS/Windows）或Docker Engine（Linux）正在运行
2. **后端服务可用**：nginx.conf中配置了代理到 `http://host.docker.internal:8088/`，需要确保本地有后端服务在8088端口运行
3. **项目文件完整**：当前目录应包含所有源代码

## 详细部署步骤

### 1. 检查Docker状态

```bash
docker --version
docker info
```

### 2. 构建Docker镜像

```bash
# 在项目根目录（包含Dockerfile的目录）执行
docker build -t sky-vue-app .
```

### 3. 运行容器

```bash
# 映射容器80端口到本地端口（例如8080）
docker run -d -p 8080:80 --name sky-vue-container sky-vue-app
```

### 4. 验证部署

```bash
# 查看容器运行状态
docker ps

# 查看容器日志
docker logs sky-vue-container

# 访问应用
# 管理端：http://localhost:8080/
# 客户端：http://localhost:8080/h5/
```

## 重要注意事项

1. **后端服务连接**：nginx配置使用了 `host.docker.internal`来访问宿主机服务，这适用于macOS/Windows的Docker Desktop。如果后端不在本地8088端口运行，需要修改nginx.conf中的代理地址
2. **网络配置**：如果后端服务也在Docker中运行，需要使用Docker网络连接而不是 `host.docker.internal`
3. **构建缓存**：首次构建可能需要较长时间下载Node和Nginx基础镜像
4. **资源占用**：该镜像包含两个Vue应用的构建结果，体积可能较大

## 故障排除

- **端口冲突**：如果8080端口被占用，修改 `-p`参数为其他端口，如 `-p 8081:80`
- **构建失败**：检查Node版本兼容性，Dockerfile中管理端使用Node 16，客户端使用Node 20
- **代理错误**：如果API请求失败，确认后端服务是否在 `http://host.docker.internal:8088/`可用

这个部署方案已经考虑了项目的具体配置。如果你确认后端服务已经就绪，并且Docker环境正常，我可以指导你执行具体的部署命令。

请确认：

1. 本地是否有后端服务在8088端口运行？
2. Docker环境是否已准备好？

如果一切就绪，你可以切换我到Act Mode来执行具体的部署操作。
