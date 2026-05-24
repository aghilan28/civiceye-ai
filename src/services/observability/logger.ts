import { createId, nowIso } from "@/lib/time";

export type LogLevel = "debug" | "info" | "warn" | "error" | "critical";

export type StructuredLog = {
  id: string;
  level: LogLevel;
  message: string;
  timestamp: string;
  service: string;
  correlationId?: string;
  metadata?: Record<string, unknown>;
};

export type LoggerOptions = {
  service: string;
  correlationId?: string;
};

const levelPriority: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
  critical: 50
};

function minimumLevel(): LogLevel {
  return process.env.NODE_ENV === "production" ? "info" : "debug";
}

export class CivicLogger {
  private readonly service: string;
  private readonly correlationId?: string;

  constructor(options: LoggerOptions) {
    this.service = options.service;
    this.correlationId = options.correlationId;
  }

  child(options: Partial<LoggerOptions>) {
    return new CivicLogger({
      service: options.service ?? this.service,
      correlationId: options.correlationId ?? this.correlationId
    });
  }

  debug(message: string, metadata?: Record<string, unknown>) {
    this.write("debug", message, metadata);
  }

  info(message: string, metadata?: Record<string, unknown>) {
    this.write("info", message, metadata);
  }

  warn(message: string, metadata?: Record<string, unknown>) {
    this.write("warn", message, metadata);
  }

  error(message: string, metadata?: Record<string, unknown>) {
    this.write("error", message, metadata);
  }

  critical(message: string, metadata?: Record<string, unknown>) {
    this.write("critical", message, metadata);
  }

  private write(level: LogLevel, message: string, metadata?: Record<string, unknown>) {
    if (levelPriority[level] < levelPriority[minimumLevel()]) {
      return;
    }

    const log: StructuredLog = {
      id: createId("LOG"),
      level,
      message,
      timestamp: nowIso(),
      service: this.service,
      correlationId: this.correlationId,
      metadata
    };

    const output = JSON.stringify(log);

    if (level === "error" || level === "critical") {
      console.error(output);
      return;
    }

    if (level === "warn") {
      console.warn(output);
      return;
    }

    console.info(output);
  }
}

export const logger = new CivicLogger({ service: "civiceye-web" });
