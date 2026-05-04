"use client";

import { supabase } from "@/lib/supabase";
import type { CreatedVideo, Job, VideoDetail, VideoListItem } from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function authHeaders(): Promise<Record<string, string>> {
  if (!supabase) return {};
  const {
    data: { session }
  } = await supabase.auth.getSession();
  return session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const tokenHeaders = await authHeaders();
  Object.entries(tokenHeaders).forEach(([key, value]) => headers.set(key, value));

  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store"
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch {
      // Keep the HTTP status text.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export function createVideoFromUrl(url: string) {
  return request<CreatedVideo>("/videos/from-url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });
}

export function createVideoFromLocal(path: string) {
  return request<CreatedVideo>("/videos/from-local", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path })
  });
}

export async function uploadVideo(file: File) {
  const headers = await authHeaders();
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/videos/upload`, {
    method: "POST",
    headers,
    body: formData
  });
  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch {
      // Keep the HTTP status text.
    }
    throw new Error(message);
  }
  return response.json() as Promise<CreatedVideo>;
}

export function listVideos() {
  return request<VideoListItem[]>("/videos");
}

export function getVideo(videoId: string) {
  return request<VideoDetail>(`/videos/${videoId}`);
}

export function getJob(jobId: string) {
  return request<Job>(`/jobs/${jobId}`);
}
