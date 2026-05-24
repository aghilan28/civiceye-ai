import { createId } from "@/lib/time";
import { yolov8Service, type YoloInferenceInput } from "@/services/mlops/yolov8-service";
import type { ModelInferenceResult } from "@/types/mlops";

export type InferenceJob = {
  id: string;
  input: YoloInferenceInput;
  status: "queued" | "running" | "completed" | "failed";
  attempts: number;
};

export class InferenceQueue {
  private readonly queue: InferenceJob[] = [];
  private running = false;
  private readonly maxAttempts = 2;

  enqueue(input: YoloInferenceInput) {
    const job: InferenceJob = {
      id: createId("JOB"),
      input,
      status: "queued",
      attempts: 0
    };
    this.queue.push(job);
    return job;
  }

  async processNext(): Promise<ModelInferenceResult | null> {
    if (this.running) {
      return null;
    }

    const job = this.queue.shift();
    if (!job) {
      return null;
    }

    this.running = true;
    job.status = "running";
    job.attempts += 1;

    try {
      const result = await yolov8Service.infer(job.input);
      job.status = "completed";
      return result;
    } catch (error) {
      job.status = "failed";
      if (job.attempts < this.maxAttempts) {
        this.queue.unshift(job);
      }
      throw error;
    } finally {
      this.running = false;
    }
  }
}

export const inferenceQueue = new InferenceQueue();
