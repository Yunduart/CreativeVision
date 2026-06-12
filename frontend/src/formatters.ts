export function formatFrameRate(frameRate: number): string {
  if (Number.isInteger(frameRate)) {
    return `${frameRate}fps`;
  }
  return `${Number(frameRate.toFixed(2))}fps`;
}

export function formatFileSize(sizeBytes: number): string {
  if (sizeBytes < 1024) {
    return `${sizeBytes} B`;
  }
  const kilobytes = sizeBytes / 1024;
  if (kilobytes < 1024) {
    return `${formatNumber(kilobytes)} KB`;
  }
  return `${formatNumber(kilobytes / 1024)} MB`;
}

export function formatCreatedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function formatNumber(value: number): string {
  return Number.isInteger(value) ? value.toString() : value.toFixed(1);
}
