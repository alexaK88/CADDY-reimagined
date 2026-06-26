export function formatList(values: string[]) {
  if (values.length === 0) {
    return "-";
  }

  return values.join(", ");
}

export function formatNullable(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return String(value);
}

export function formatElapsedTime(value: number) {
  return `${value.toFixed(1)}s`;
}

export function formatDateTime(value: Date | null) {
  if (value === null) {
    return "-";
  }

  return value.toLocaleTimeString();
}

export function prettifyEnum(value: string | null | undefined) {
  if (!value) {
    return "-";
  }

  return value.replaceAll("_", " ");
}