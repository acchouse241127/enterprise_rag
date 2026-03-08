"""
Docker 动态挂载服务

通过 Docker SDK 动态重新创建容器并添加 volume 挂载。

Author: C2
Date: 2026-03-07
"""

import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

import docker
from docker.errors import DockerException, NotFound, APIError

from app.config import settings


class DockerMountService:
    """Docker 动态挂载服务"""

    @classmethod
    def _validate_path(cls, path_str: str) -> tuple[bool, str | None]:
        """
        验证路径合法性。

        检查项目：
        1. 目录遍历防护（检查 ..）- 必须在规范化前检查
        2. 网络路径防护（UNC 路径）
        3. 路径存在性
        4. 路径类型（必须是目录）
        5. 路径前缀限制（如果配置了允许的前缀）
        6. Windows 系统目录保护

        Args:
            path_str: 待验证的路径

        Returns:
            (是否有效, 错误消息)
        """
        try:
            # 1. 目录遍历防护 - 必须在 Path.resolve() 之前检查
            if ".." in Path(path_str).parts:
                return False, "路径包含非法的父目录引用"

            # 2. 网络路径防护 - 阻止 UNC 路径 (\\server\share 或 //server/share)
            if path_str.startswith("\\\\") or path_str.startswith("//"):
                return False, "不允许挂载网络路径"

            # 3. 规范化路径
            path = Path(path_str).resolve()

            # 4. 检测是否在容器内运行
            # Docker 容器会创建 /.dockerenv 文件，可以通过它来检测
            is_in_container = Path("/.dockerenv").exists()

            # 5. 路径存在性和类型检查
            # 如果在容器内，跳过这些检查（容器无法访问宿主机路径）
            # Docker 挂载时会验证路径是否可访问
            if not is_in_container:
                if not path.exists():
                    return False, f"路径不存在: {path_str}"
                if not path.is_dir():
                    return False, f"路径必须是目录: {path_str}"

            # 4. 路径前缀限制
            allowed_prefixes_str = settings.docker_allowed_path_prefixes
            if allowed_prefixes_str:
                allowed_prefixes = [
                    p.strip() for p in allowed_prefixes_str.split(",") if p.strip()
                ]
                if allowed_prefixes:
                    path_str_normalized = os.path.normpath(path_str)
                    is_allowed = any(
                        path_str_normalized.startswith(os.path.normpath(prefix))
                        for prefix in allowed_prefixes
                    )
                    if not is_allowed:
                        return False, f"路径不在允许的目录前缀列表中: {allowed_prefixes}"

            # 6. Windows 系统目录保护
            if platform.system() == "Windows":
                # 获取系统目录路径 - 包含更多关键系统目录
                system_paths = [
                    os.environ.get("SystemRoot", r"C:\Windows"),
                    os.environ.get("ProgramFiles", r"C:\Program Files"),
                    os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                    os.environ.get("ProgramData", r"C:\ProgramData"),
                    os.environ.get("USERPROFILE", ""),  # 用户配置文件根目录
                    r"C:\System Volume Information",  # 系统还原数据
                    r"C:\Recovery",  # 恢复分区
                    r"C:\Boot",  # 启动分区
                ]
                # 转换为 Path 对象进行规范化比较
                system_path_objs = [Path(p).resolve() for p in system_paths if p]
                for sys_path in system_path_objs:
                    try:
                        if path == sys_path or path.is_relative_to(sys_path):
                            return False, f"不允许挂载系统目录: {sys_path}"
                    except AttributeError:
                        # is_relative_to 在 Python 3.9+ 才有
                        try:
                            if path == sys_path or str(path).startswith(str(sys_path)):
                                return False, f"不允许挂载系统目录: {sys_path}"
                        except (TypeError, ValueError):
                            pass

            return True, None

        except (OSError, ValueError) as e:
            return False, f"路径验证失败: {e!s}"

    @classmethod
    def _get_client(cls) -> docker.DockerClient:
        """
        获取 Docker 客户端。

        Returns:
            Docker 客户端实例

        Raises:
            DockerException: Docker 连接失败
        """
        try:
            return docker.from_env()
        except DockerException as e:
            raise DockerException(f"无法连接到 Docker: {e!s}") from e

    @classmethod
    def get_docker_status(cls) -> dict[str, Any]:
        """
        获取 Docker 和容器状态。

        Returns:
            Docker 状态字典
        """
        try:
            client = cls._get_client()
            version = client.version()

            backend_status = cls._get_container_status(
                client, settings.docker_backend_container_name
            )
            worker_status = cls._get_container_status(
                client, settings.docker_worker_container_name
            )

            return {
                "success": True,
                "docker_version": version.get("Version", "unknown"),
                "api_version": version.get("ApiVersion", "unknown"),
                "os": version.get("Os", "unknown"),
                "backend": backend_status,
                "worker": worker_status,
                "enabled": settings.docker_dynamic_mount_enabled,
            }
        except DockerException as e:
            return {
                "success": False,
                "message": f"Docker 连接失败: {e!s}",
                "enabled": settings.docker_dynamic_mount_enabled,
            }

    @classmethod
    def _get_container_status(
        cls, client: docker.DockerClient, container_name: str
    ) -> dict[str, Any]:
        """
        获取容器状态。

        Args:
            client: Docker 客户端
            container_name: 容器名称

        Returns:
            容器状态字典
        """
        try:
            container = client.containers.get(container_name)
            return {
                "name": container_name,
                "status": container.status,
                "running": container.status == "running",
                "image": container.image.tags[0] if container.image.tags else "unknown",
            }
        except NotFound:
            return {
                "name": container_name,
                "status": "not_found",
                "running": False,
                "image": "unknown",
            }
        except APIError as e:
            return {
                "name": container_name,
                "status": f"error: {e!s}",
                "running": False,
                "image": "unknown",
            }

    @classmethod
    def _extract_ports(cls, container_attrs: dict[str, Any]) -> dict[str, Any]:
        """
        从容器属性中提取端口映射。

        Args:
            container_attrs: 容器属性字典

        Returns:
            端口映射字典
        """
        ports: dict[str, Any] = {}
        network_settings = container_attrs.get("NetworkSettings", {})
        ports_dict = network_settings.get("Ports", {})
        for container_port, host_bindings in ports_dict.items():
            if host_bindings:
                ports[container_port] = host_bindings[0].get("HostPort")
        return ports

    @classmethod
    def _extract_volumes(cls, container_attrs: dict[str, Any]) -> dict[str, Any]:
        """
        从容器属性中提取 volume 挂载。

        Args:
            container_attrs: 容器属性字典

        Returns:
            volume 挂载字典
        """
        mounts: dict[str, Any] = {}
        host_config = container_attrs.get("HostConfig", {})
        binds = host_config.get("Binds", [])
        for bind in binds:
            # bind 格式: "host_path:container_path:rw"
            if ":" in bind:
                parts = bind.split(":")
                if len(parts) >= 2:
                    host_path = parts[0]
                    container_path = parts[1]
                    mode = parts[2] if len(parts) > 2 else "rw"
                    mounts[container_path] = {"bind": host_path, "mode": mode}
        return mounts

    @classmethod
    def mount_volume(
        cls,
        host_path: str,
        container_path: str,
        container_name: str = "enterprise_rag_backend",
    ) -> dict[str, Any]:
        """
        通过重新创建容器实现动态挂载。

        流程：
        1. 验证路径
        2. 获取当前容器配置
        3. 添加新的 volume 挂载到配置
        4. 停止旧容器
        5. 创建新容器（带新挂载）
        6. 启动新容器

        Args:
            host_path: 宿主机路径
            container_path: 容器内路径
            container_name: 容器名称

        Returns:
            操作结果字典
        """
        # 检查功能是否启用
        if not settings.docker_dynamic_mount_enabled:
            return {"success": False, "message": "Docker 动态挂载功能未启用"}

        # 验证路径
        is_valid, error = cls._validate_path(host_path)
        if not is_valid:
            return {"success": False, "message": error}

        try:
            client = cls._get_client()

            # 获取当前容器
            container = client.containers.get(container_name)
            old_config = container.attrs

            # 检查是否已存在相同挂载
            existing_mounts = old_config.get("HostConfig", {}).get("Binds", [])
            new_bind = f"{host_path}:{container_path}:rw"
            if any(new_bind in bind for bind in existing_mounts):
                return {
                    "success": True,
                    "message": "路径已挂载",
                    "container_path": container_path,
                    "container_name": container_name,
                }

            # 构建新配置
            old_host_config = old_config.get("HostConfig", {})

            # 添加新的 volume 挂载
            old_binds = old_host_config.get("Binds", [])
            new_binds = old_binds + [new_bind]
            old_host_config["Binds"] = new_binds

            # 保存容器镜像（用于重新创建）
            image_name = old_config["Image"]
            container_name_new = f"{container_name}_temp_{int(time.time())}"

            # 提取环境变量
            env = old_config.get("Config", {}).get("Env", [])

            # 提取端口映射
            ports = cls._extract_ports(old_config)

            # 将 Binds 转换为 mounts 格式
            # binds 格式: "host_path:container_path:rw"
            # mounts 格式: {"Source": "host_path", "Target": "container_path", "Type": "bind", "RW": True}
            mounts = []
            for bind in new_binds:
                parts = bind.split(":")
                if len(parts) >= 2:
                    mounts.append({
                        "Source": parts[0],
                        "Target": parts[1].rstrip(":rw"),
                        "Type": "bind",
                        "RW": len(parts) < 3 or parts[2] == "rw"
                    })

            # 创建临时容器
            # 注意：不设置 network，让 Docker 使用默认网络（docker-compose 会自动连接到 rag_network）
            new_container = client.containers.create(
                image=image_name,
                name=container_name_new,
                mounts=mounts,
                environment=env,
                ports=ports,
                detach=True,
                # 保持工作目录一致
                working_dir=old_config.get("Config", {}).get("WorkingDir", "/app"),
            )

            # 停止并删除旧容器
            container.stop(timeout=settings.docker_restart_timeout)
            container.remove()

            # 重命名新容器
            new_container.rename(container_name)

            # 启动新容器，并等待运行状态
            new_container.start()
            start_time = time.time()
            while new_container.status != "running":
                if time.time() - start_time > settings.docker_restart_timeout:
                    raise DockerException("容器启动超时")
                new_container.reload()
                time.sleep(0.5)

            return {
                "success": True,
                "message": "挂载成功，容器已重新创建",
                "container_name": container_name,
                "container_path": container_path,
                "host_path": host_path,
            }

        except NotFound:
            return {
                "success": False,
                "message": f"容器不存在: {container_name}",
            }
        except DockerException as e:
            # 提供用户友好的错误消息
            error_str = str(e).lower()
            if "permission" in error_str:
                user_msg = "权限不足，请检查 Docker socket 权限"
            elif "not found" in error_str:
                user_msg = "Docker 资源不存在"
            elif "timeout" in error_str:
                user_msg = "操作超时，请稍后重试"
            elif "already in use" in error_str:
                user_msg = "容器名称已被占用"
            else:
                user_msg = "Docker 操作失败"
            return {
                "success": False,
                "message": user_msg,
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Docker mount failed: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"操作失败: {e!s}",
            }

    @classmethod
    def restart_container(
        cls, container_name: str = "enterprise_rag_backend"
    ) -> dict[str, Any]:
        """
        重启容器。

        Args:
            container_name: 容器名称

        Returns:
            操作结果字典
        """
        # 检查功能是否启用
        if not settings.docker_dynamic_mount_enabled:
            return {"success": False, "message": "Docker 动态挂载功能未启用"}

        try:
            client = cls._get_client()
            container = client.containers.get(container_name)

            container.restart(timeout=settings.docker_restart_timeout)

            return {
                "success": True,
                "message": "容器重启成功",
                "container_name": container_name,
            }
        except NotFound:
            return {
                "success": False,
                "message": f"容器不存在: {container_name}",
            }
        except DockerException as e:
            error_str = str(e).lower()
            if "permission" in error_str:
                user_msg = "权限不足，请检查 Docker socket 权限"
            elif "timeout" in error_str:
                user_msg = "重启超时，请稍后重试"
            else:
                user_msg = "重启容器失败"
            return {
                "success": False,
                "message": user_msg,
            }
