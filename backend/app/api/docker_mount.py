"""
Docker 挂载 API

提供动态挂载 Docker volume 的 API 接口。

Author: C2
Date: 2026-03-07
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_editor_user
from app.config import settings
from app.models.user import User
from app.services.docker_mount_service import DockerMountService

router = APIRouter()

# 允许重启的容器白名单
ALLOWED_CONTAINERS = [
    settings.docker_backend_container_name,
    settings.docker_worker_container_name,
]


class MountVolumeRequest(BaseModel):
    """请求挂载 volume 的请求体."""
    host_path: str = Field(..., description="宿主机路径")
    container_path: str | None = Field(None, description="容器内路径，默认自动生成")


class DockerMountResponse(BaseModel):
    """挂载操作的响应模型."""
    success: bool
    message: str
    container_name: str | None = None
    container_path: str | None = None
    host_path: str | None = None


class DockerStatusResponse(BaseModel):
    """Docker 状态响应模型."""
    success: bool
    docker_version: str | None = None
    api_version: str | None = None
    os: str | None = None
    backend: dict | None = None
    worker: dict | None = None
    enabled: bool = True
    message: str | None = None


class RestartContainerResponse(BaseModel):
    """重启容器响应模型."""
    success: bool
    message: str
    container_name: str | None = None


@router.get("/status", response_model=DockerStatusResponse)
def get_docker_status(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    获取 Docker 和容器状态.

    需要登录用户权限。
    """
    status = DockerMountService.get_docker_status()
    return status


@router.post("/mount/{knowledge_base_id}", response_model=DockerMountResponse)
def mount_volume(
    knowledge_base_id: int,
    body: MountVolumeRequest,
    current_user: User = Depends(get_editor_user),
) -> dict:
    """
    动态挂载 volume 到 Docker 容器.

    通过重新创建容器的方式实现动态挂载。

    Args:
        knowledge_base_id: 知识库 ID（用于生成默认容器路径）
        body: 挂载请求

    权限：
        需要 admin 或 editor 角色

    流程：
        1. 验证宿主机路径合法性
        2. 生成容器内路径（如未提供）
        3. 检查是否已挂载
        4. 停止旧容器
        5. 创建新容器（带新挂载）
        6. 启动新容器
    """
    # 生成容器内路径
    container_path = body.container_path or f"/data/sync/{knowledge_base_id}"

    result = DockerMountService.mount_volume(
        host_path=body.host_path,
        container_path=container_path,
        container_name="enterprise_rag_backend",
    )

    return result


@router.post("/restart/{container_name}", response_model=RestartContainerResponse)
def restart_container(
    container_name: str,
    current_user: User = Depends(get_editor_user),
) -> dict:
    """
    重启指定的 Docker 容器.

    Args:
        container_name: 容器名称（仅允许白名单中的容器）

    权限：
        需要 admin 或 editor 角色

    安全：
        仅允许重启配置的 backend 和 worker 容器
    """
    # 验证容器名称在白名单中
    if container_name not in ALLOWED_CONTAINERS:
        raise HTTPException(
            status_code=403,
            detail=f"不允许重启容器: {container_name}"
        )

    result = DockerMountService.restart_container(container_name)
    return result
