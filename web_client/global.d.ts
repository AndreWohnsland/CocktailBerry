interface FilePickerAcceptType {
  description?: string;
  accept: Record<string, string[]>;
}

interface FilePickerOptions {
  multiple?: boolean;
  excludeAcceptAllOption?: boolean;
  types?: FilePickerAcceptType[];
}

interface OpenFilePickerOptions extends FilePickerOptions {}

interface SaveFilePickerOptions extends FilePickerOptions {
  suggestedName?: string;
}

interface FileSystemFileHandle {
  getFile(): Promise<File>;
  createWritable(): Promise<FileSystemWritableFileStream>;
}

interface FileSystemWritableFileStream {
  write(data: BufferSource | Blob | string): Promise<void>;
  close(): Promise<void>;
}

interface Window {
  showSaveFilePicker: (options?: SaveFilePickerOptions) => Promise<FileSystemFileHandle>;
  showOpenFilePicker: (options?: OpenFilePickerOptions) => Promise<FileSystemFileHandle[]>;
}
