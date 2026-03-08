/**
 * Docker 部署辅助工具
 * 用于生成 Docker volume 挂载命令
 */

/**
 * 生成容器内同步路径
 * @param kbId 知识库 ID
 * @returns 容器内路径，例如 /app/data/uploads/sync/123
 */
export function generateContainerPath(kbId: number): string {
  return `/app/data/uploads/sync/${kbId}`;
}

/**
 * Docker 挂载配置接口
 */
export interface DockerMountConfig {
  hostPath: string;      // 宿主机路径
  containerPath: string; // 容器内路径
  kbId: number;          // 知识库 ID
  kbName?: string;       // 知识库名称（可选，用于注释）
}

/**
 * 生成 docker run -v 参数
 */
export function generateDockerRunVolume(config: DockerMountConfig): string {
  return `-v "${config.hostPath}:${config.containerPath}"`;
}

/**
 * 生成完整的 docker run 命令示例
 */
export function generateDockerRunCommand(config: DockerMountConfig): string {
  const volume = generateDockerRunVolume(config);
  const comment = config.kbName 
    ? `# 知识库: ${config.kbName} (ID: ${config.kbId})\n` 
    : "";
  
  return `${comment}docker run -d \\
  --name enterprise-rag \\
  ${volume} \\
  -p 8000:8000 \\
  enterprise-rag:latest`;
}

/**
 * 生成 docker-compose volumes 片段
 */
export function generateDockerComposeVolume(config: DockerMountConfig): string {
  const comment = config.kbName 
    ? `      # 知识库: ${config.kbName} (ID: ${config.kbId})\n` 
    : "";
  
  return `${comment}      - "${config.hostPath}:${config.containerPath}"`;
}

/**
 * 生成完整的 docker-compose.yml volumes 配置示例
 */
export function generateDockerComposeSnippet(config: DockerMountConfig): string {
  const volumeLine = generateDockerComposeVolume(config);
  
  return `services:
  backend:
    volumes:
      ${volumeLine}
      # ... 其他 volumes ...
`;
}

/**
 * 生成完整的 Docker 配置指南
 */
export function generateDockerGuide(config: DockerMountConfig): {
  runCommand: string;
  composeSnippet: string;
  instructions: string[];
} {
  return {
    runCommand: generateDockerRunCommand(config),
    composeSnippet: generateDockerComposeSnippet(config),
    instructions: [
      "1. 复制上方的 Docker 命令或 docker-compose 配置",
      "2. 在宿主机终端执行命令，或更新 docker-compose.yml 后执行 docker-compose up -d",
      "3. 重启容器使挂载生效",
      "4. 返回此页面点击「立即同步」测试",
    ],
  };
}

/**
 * 复制文本到剪贴板
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // 降级方案：使用 execCommand
    try {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      return true;
    } catch {
      return false;
    }
  }
}
