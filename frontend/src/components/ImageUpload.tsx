import { useCallback, useEffect, useState, useRef } from 'react';
import { Upload, ImageIcon, X, Camera } from 'lucide-react';

interface Props {
  onFileSelect: (file: File | null) => void;
  selectedFile: File | null;
}

export default function ImageUpload({ onFileSelect, selectedFile }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [cameraMode, setCameraMode] = useState(false);
  const [cameraAvailable, setCameraAvailable] = useState(Boolean(navigator.mediaDevices?.getUserMedia));
  const inputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => stopStream();
  }, [stopStream]);

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
    onFileSelect(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const handleStartCamera = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraAvailable(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      setCameraMode(true);
      requestAnimationFrame(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          void videoRef.current.play();
        }
      });
    } catch {
      setCameraAvailable(false);
      stopStream();
    }
  };

  const handleCancelCamera = (e: React.MouseEvent) => {
    e.stopPropagation();
    stopStream();
    setCameraMode(false);
  };

  const handleCapture = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!videoRef.current) return;

    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;

    const context = canvas.getContext('2d');
    if (!context) return;

    context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const capturedFile = new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' });
        handleFile(capturedFile);
        stopStream();
        setCameraMode(false);
      },
      'image/jpeg',
      0.92,
    );
  };

  return (
    <div
      className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={cameraMode ? undefined : handleClick}
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

      {cameraMode ? (
        <div style={{ width: '100%' }}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{ width: '100%', maxHeight: 380, objectFit: 'cover', borderRadius: 14 }}
          />
          <div style={{ display: 'flex', gap: 10, marginTop: 12, justifyContent: 'center' }}>
            <button className="btn btn-primary" onClick={handleCapture}>Capture</button>
            <button className="btn btn-ghost" onClick={handleCancelCamera}>Cancel</button>
          </div>
        </div>
      ) : preview ? (
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
            <span style={{ color: 'var(--accent-amber)' }}>
              Strictly front-facing, well-lit selfies only. Side profiles or obscured faces will be rejected by the AI.
            </span>
          </p>
          {cameraAvailable && (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={handleStartCamera}
              style={{ marginTop: 12 }}
            >
              <Camera size={16} />
              Use Camera
            </button>
          )}
        </>
      )}
    </div>
  );
}
