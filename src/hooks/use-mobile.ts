"use client";

import { useMediaQuery } from "@/hooks/use-media-query";

export function useMobile() {
  return useMediaQuery("(max-width: 767px)");
}
