interface Props {
  base64Image: string;
}

export default function CanvasOverlay({ base64Image }: Props) {
  return (
    <div className="annotated-image-container glass-card" style={{ padding: 0, overflow: 'hidden' }}>
      <img
        src={`data:image/png;base64,${base64Image}`}
        alt="Annotated skin analysis"
        className="annotated-image"
        id="annotated-result-image"
      />
    </div>
  );
}
