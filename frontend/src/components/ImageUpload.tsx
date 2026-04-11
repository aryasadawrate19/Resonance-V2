import { useCallback, useState, useRef } from 'react';
import { Upload, ImageIcon, X } from 'lucide-react';

interface Props {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
}

export default function ImageUpload({ onFileSelect, selectedFile }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) return;
    onFileSelect(file);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);
  }, [onFileSelect]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragOver(false), []);

  const handleClick = () => inputRef.current?.click();

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    setPreview(null);
    onFileSelect(null as unknown as File);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div
      className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleClick}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
        style={{ display: 'none' }}
        id="image-upload-input"
      />

      {preview ? (
        <div style={{ position: 'relative', display: 'inline-block' }}>
          <img src={preview} alt="Preview" className="upload-preview" />
          <button
            onClick={handleClear}
            className="btn btn-ghost"
            style={{
              position: 'absolute',
              top: 8,
              right: 8,
              background: 'rgba(0,0,0,0.6)',
              borderRadius: '50%',
              padding: 6,
            }}
          >
            <X size={16} />
          </button>
          <p style={{ marginTop: 12, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {selectedFile?.name}
          </p>
        </div>
      ) : (
        <>
          <div className="upload-icon">
            {dragOver ? <ImageIcon size={64} /> : <Upload size={64} />}
          </div>
          <h3 style={{ marginBottom: 8 }}>
            {dragOver ? 'Drop your image here' : 'Upload a face photo'}
          </h3>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Drag & drop or click to browse • JPEG, PNG, WebP
          </p>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 8 }}>
            Best results: front-facing, well-lit, clear selfie
          </p>
        </>
      )}
    </div>
  );
}
