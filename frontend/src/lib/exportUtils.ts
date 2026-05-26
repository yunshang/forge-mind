export function exportCode(code: string, filename: string): void {
  if (!code) {
    console.warn("No code to export");
    return;
  }

  const blob = new Blob([code], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${filename || "contract"}.sol`;
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export async function exportImage(
  element: HTMLElement,
  filename: string
): Promise<void> {
  if (!element) {
    console.warn("No element to export");
    return;
  }

  try {
    const { toPng } = await import("html-to-image");
    
    const dataUrl = await toPng(element, {
      backgroundColor: "#030712",
      quality: 1.0,
      pixelRatio: 2,
      cacheBust: true,
    });
    
    const link = document.createElement("a");
    link.href = dataUrl;
    link.download = `${filename || "export"}.png`;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    console.error("Failed to export image:", error);
    throw error;
  }
}

export async function exportReactFlowImage(
  reactFlowElement: HTMLElement,
  filename: string
): Promise<void> {
  await exportImage(reactFlowElement, filename);
}
