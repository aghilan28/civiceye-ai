import { createId, nowIso } from "@/lib/time";
import { realtimeClient } from "@/services/realtime/realtime-client";
import type { CivicNotification, NotificationCategory } from "@/types/operations";

export const notificationService = {
  create(category: NotificationCategory, title: string, body: string, incidentId?: string): CivicNotification {
    const notification: CivicNotification = {
      id: createId("NOT"),
      category,
      title,
      body,
      incidentId,
      unread: true,
      createdAt: nowIso()
    };

    realtimeClient.publish({ type: "notification.created", notification });
    return notification;
  },

  markAllRead(notifications: CivicNotification[]) {
    return notifications.map((notification) => ({ ...notification, unread: false }));
  }
};
