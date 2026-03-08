/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_API_BASE: string;
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// File System Access API 类型声明
interface Window {
  showDirectoryPicker(options?: {
    mode?: "read" | "readwrite";
    startIn?: "desktop" | "documents" | "downloads" | "music" | "pictures" | "videos";
  }): Promise<FileSystemDirectoryHandle>;
}

interface FileSystemDirectoryHandle {
  name: string;
}
